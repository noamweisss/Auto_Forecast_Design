"""Structured, retrying acquisition of IMS forecast feeds.

The public ``fetch_feed`` function returns either XML or a readable failure;
callers never have to guess why a request returned ``None``. Network and sleep
functions are ordinary injected arguments so the automated suite stays offline.
"""

from dataclasses import dataclass
from enum import Enum
import logging
import re
import time
from typing import Callable, Optional

import requests

from src.data.snapshots import FeedType


logger = logging.getLogger(__name__)

COUNTRY_FORECAST_URL = (
    "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_country.xml"
)
CITIES_FORECAST_URL = (
    "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_cities.xml"
)

_FEED_URLS = {
    FeedType.COUNTRY: COUNTRY_FORECAST_URL,
    FeedType.CITIES: CITIES_FORECAST_URL,
}
_DECODING_ORDER = ("utf-8", "windows-1255", "iso-8859-8")
_ENCODING_ALIASES = {
    "utf-8": "utf-8",
    "utf8": "utf-8",
    "windows-1255": "windows-1255",
    "cp1255": "windows-1255",
    "iso-8859-8": "iso-8859-8",
    "iso8859-8": "iso-8859-8",
}


class FetchFailureKind(str, Enum):
    TIMEOUT = "timeout"
    HTTP = "http"
    CONNECTION = "connection"
    REQUEST = "request"
    DECODE = "decode"


@dataclass(frozen=True)
class FetchFailure:
    """A readable reason one fetch attempt failed, kept for the caller."""

    kind: FetchFailureKind
    message: str
    status_code: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, FetchFailureKind):
            raise ValueError("kind must be a FetchFailureKind")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be nonempty")


@dataclass(frozen=True)
class FetchResult:
    """Exactly one of decoded ``xml`` or a structured ``failure`` for one feed."""

    feed_type: FeedType
    url: str
    attempt_count: int
    xml: Optional[str] = None
    failure: Optional[FetchFailure] = None

    def __post_init__(self) -> None:
        if not isinstance(self.feed_type, FeedType):
            raise ValueError("feed_type must be a FeedType")
        if not isinstance(self.url, str) or not self.url.strip():
            raise ValueError("url must be nonempty")
        if not isinstance(self.attempt_count, int) or self.attempt_count <= 0:
            raise ValueError("attempt_count must be positive")
        if (self.xml is None) == (self.failure is None):
            raise ValueError("FetchResult requires exactly one of xml or failure")
        if self.xml is not None and not isinstance(self.xml, str):
            raise ValueError("xml must be a string")
        if self.failure is not None and not isinstance(self.failure, FetchFailure):
            raise ValueError("failure must be a FetchFailure")
        if self.xml is not None and not self.xml:
            raise ValueError("xml must be nonempty")

    @property
    def succeeded(self) -> bool:
        return self.xml is not None


def fetch_feed(
    feed_type: FeedType,
    *,
    request_get: Callable = requests.get,
    sleep: Callable[[float], None] = time.sleep,
    timeout_seconds: float = 30,
    retry_delays: tuple[float, ...] = (30, 60),
) -> FetchResult:
    """Fetch one IMS feed with explicit retries and structured failure details."""
    if not isinstance(feed_type, FeedType):
        raise ValueError("feed_type must be a FeedType")

    url = _FEED_URLS[feed_type]
    total_attempts = 1 + len(retry_delays)
    final_failure: Optional[FetchFailure] = None

    for attempt_count in range(1, total_attempts + 1):
        logger.info("Fetching %s feed, attempt %s/%s", feed_type.value, attempt_count, total_attempts)
        retryable = True
        try:
            response = request_get(url, timeout=timeout_seconds)
            status_code = response.status_code
            if status_code >= 400:
                final_failure = FetchFailure(
                    kind=FetchFailureKind.HTTP,
                    message=f"IMS returned HTTP {status_code}",
                    status_code=status_code,
                )
                retryable = status_code >= 500
            else:
                xml = _decode_xml(response.content)
                if not xml.strip():
                    final_failure = FetchFailure(
                        FetchFailureKind.DECODE,
                        "IMS returned an empty response body",
                    )
                else:
                    return FetchResult(
                        feed_type=feed_type,
                        url=url,
                        attempt_count=attempt_count,
                        xml=xml,
                    )
        except requests.exceptions.Timeout as error:
            final_failure = FetchFailure(
                FetchFailureKind.TIMEOUT,
                f"IMS request timed out: {error}",
            )
        except requests.exceptions.ConnectionError as error:
            final_failure = FetchFailure(
                FetchFailureKind.CONNECTION,
                f"Could not connect to IMS: {error}",
            )
        except requests.exceptions.RequestException as error:
            final_failure = FetchFailure(
                FetchFailureKind.REQUEST,
                f"IMS request failed: {error}",
            )
        except UnicodeError as error:
            final_failure = FetchFailure(
                FetchFailureKind.DECODE,
                f"IMS response could not be decoded: {error}",
            )

        if not retryable or attempt_count == total_attempts:
            assert final_failure is not None
            return FetchResult(
                feed_type=feed_type,
                url=url,
                attempt_count=attempt_count,
                failure=final_failure,
            )

        delay = retry_delays[attempt_count - 1]
        logger.info("Waiting %s seconds before retry", delay)
        sleep(delay)

    raise AssertionError("fetch retry loop did not return")


def _decode_xml(content: bytes) -> str:
    declaration = re.search(
        br"<\?xml[^>]*encoding\s*=\s*['\"]([^'\"]+)['\"]",
        content[:256],
        flags=re.IGNORECASE,
    )
    declared_encoding: Optional[str] = None
    if declaration:
        label = declaration.group(1).decode("ascii", errors="ignore").lower()
        declared_encoding = _ENCODING_ALIASES.get(label)
        if declared_encoding is None:
            raise UnicodeError(f"unsupported XML encoding declaration {label!r}")

    candidates = list(_DECODING_ORDER)
    if declared_encoding is not None:
        candidates.remove(declared_encoding)
        candidates.insert(0, declared_encoding)

    failures = []
    for encoding in candidates:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError as error:
            failures.append(f"{encoding}: {error.reason}")

    raise UnicodeError("; ".join(failures))
