"""Offline contracts for structured IMS feed acquisition."""

from dataclasses import replace

import pytest
import requests

from src.data.fetcher import (
    CITIES_FORECAST_URL,
    COUNTRY_FORECAST_URL,
    FetchFailure,
    FetchFailureKind,
    FetchResult,
    fetch_feed,
)
from src.data.snapshots import FeedType


class FakeResponse:
    """The response fields fetch_feed reads, with no network behavior."""

    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code


class ResponseSequence:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, *, timeout):
        self.calls.append((url, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_fetch_feed_preserves_utf8_hebrew():
    xml = '<?xml version="1.0" encoding="UTF-8"?><city>ירושלים</city>'

    result = fetch_feed(
        FeedType.CITIES,
        request_get=ResponseSequence(FakeResponse(xml.encode("utf-8"))),
        sleep=lambda _: None,
        retry_delays=(),
    )

    assert result.succeeded is True
    assert result.xml == xml
    assert result.failure is None
    assert result.attempt_count == 1


def test_fetch_feed_preserves_windows_1255_hebrew():
    xml = '<?xml version="1.0" encoding="windows-1255"?><city>ירושלים</city>'

    result = fetch_feed(
        FeedType.CITIES,
        request_get=ResponseSequence(FakeResponse(xml.encode("windows-1255"))),
        sleep=lambda _: None,
        retry_delays=(),
    )

    assert result.xml == xml


def test_xml_declaration_prevents_false_utf8_acceptance():
    payload = (
        b'<?xml version="1.0" encoding="windows-1255"?>'
        b"<value>\xc3\xa9</value>"
    )

    result = fetch_feed(
        FeedType.COUNTRY,
        request_get=ResponseSequence(FakeResponse(payload)),
        sleep=lambda _: None,
        retry_delays=(),
    )

    assert result.xml == payload.decode("windows-1255")
    assert "é" not in result.xml


def test_retry_then_success_uses_exact_delay_and_no_final_sleep():
    request_get = ResponseSequence(
        requests.exceptions.Timeout("slow"),
        FakeResponse(b"<ok />"),
    )
    sleeps = []

    result = fetch_feed(
        FeedType.COUNTRY,
        request_get=request_get,
        sleep=sleeps.append,
        retry_delays=(3, 8),
    )

    assert result.succeeded is True
    assert result.attempt_count == 2
    assert sleeps == [3]


@pytest.mark.parametrize(
    ("outcome", "kind", "status_code"),
    [
        (requests.exceptions.Timeout("slow"), FetchFailureKind.TIMEOUT, None),
        (
            requests.exceptions.ConnectionError("offline"),
            FetchFailureKind.CONNECTION,
            None,
        ),
        (requests.exceptions.RequestException("bad request"), FetchFailureKind.REQUEST, None),
        (FakeResponse(b"server error", status_code=503), FetchFailureKind.HTTP, 503),
        (FakeResponse(bytes(range(256))), FetchFailureKind.DECODE, None),
    ],
)
def test_retryable_failures_use_all_attempts_and_preserve_final_reason(
    outcome, kind, status_code
):
    request_get = ResponseSequence(outcome, outcome, outcome)
    sleeps = []

    result = fetch_feed(
        FeedType.COUNTRY,
        request_get=request_get,
        sleep=sleeps.append,
        retry_delays=(1, 2),
    )

    assert result.succeeded is False
    assert result.xml is None
    assert result.failure is not None
    assert result.failure.kind is kind
    assert result.failure.status_code == status_code
    assert result.attempt_count == 3
    assert sleeps == [1, 2]


@pytest.mark.parametrize("body", [b"", b"   \n\t "])
def test_empty_success_body_becomes_decode_failure_not_a_crash(body):
    request_get = ResponseSequence(FakeResponse(body), FakeResponse(body))
    sleeps = []

    result = fetch_feed(
        FeedType.COUNTRY,
        request_get=request_get,
        sleep=sleeps.append,
        retry_delays=(1,),
    )

    assert result.succeeded is False
    assert result.failure is not None
    assert result.failure.kind is FetchFailureKind.DECODE
    assert result.attempt_count == 2
    assert sleeps == [1]


def test_4xx_stops_immediately_without_sleeping():
    request_get = ResponseSequence(FakeResponse(b"not found", status_code=404))
    sleeps = []

    result = fetch_feed(
        FeedType.CITIES,
        request_get=request_get,
        sleep=sleeps.append,
        retry_delays=(1, 2),
    )

    assert result.failure == FetchFailure(
        kind=FetchFailureKind.HTTP,
        message="IMS returned HTTP 404",
        status_code=404,
    )
    assert result.attempt_count == 1
    assert sleeps == []


@pytest.mark.parametrize(
    ("feed_type", "expected_url"),
    [
        (FeedType.COUNTRY, COUNTRY_FORECAST_URL),
        (FeedType.CITIES, CITIES_FORECAST_URL),
    ],
)
def test_fetch_feed_selects_the_url_for_its_feed(feed_type, expected_url):
    request_get = ResponseSequence(FakeResponse(b"<ok />"))

    result = fetch_feed(
        feed_type,
        request_get=request_get,
        sleep=lambda _: None,
        timeout_seconds=17,
        retry_delays=(),
    )

    assert result.url == expected_url
    assert request_get.calls == [(expected_url, 17)]


def test_fetch_result_rejects_both_xml_and_failure():
    failure = FetchFailure(FetchFailureKind.REQUEST, "failed")

    with pytest.raises(ValueError, match="exactly one of xml or failure"):
        FetchResult(
            feed_type=FeedType.COUNTRY,
            url=COUNTRY_FORECAST_URL,
            attempt_count=1,
            xml="<ok />",
            failure=failure,
        )


def test_fetch_result_rejects_neither_xml_nor_failure():
    with pytest.raises(ValueError, match="exactly one of xml or failure"):
        FetchResult(
            feed_type=FeedType.COUNTRY,
            url=COUNTRY_FORECAST_URL,
            attempt_count=1,
        )


def test_fetch_result_rejects_nonpositive_attempt_count():
    valid = FetchResult(
        feed_type=FeedType.COUNTRY,
        url=COUNTRY_FORECAST_URL,
        attempt_count=1,
        xml="<ok />",
    )

    with pytest.raises(ValueError, match="attempt_count must be positive"):
        replace(valid, attempt_count=0)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("xml", 123, "xml must be a string"),
        ("failure", "failed", "failure must be a FetchFailure"),
    ],
)
def test_fetch_result_rejects_wrong_result_value_types(field, value, message):
    values = {
        "feed_type": FeedType.COUNTRY,
        "url": COUNTRY_FORECAST_URL,
        "attempt_count": 1,
        "xml": None,
        "failure": None,
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        FetchResult(**values)
