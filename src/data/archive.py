"""Atomic storage and metadata-based lookup for validated IMS snapshots."""

from dataclasses import replace
from datetime import date, datetime, timedelta
import json
import logging
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from src.data.snapshots import (
    FeedType,
    ForecastSnapshot,
    SnapshotSource,
    SnapshotValidationError,
    build_snapshot,
)


logger = logging.getLogger(__name__)

SNAPSHOT_SCHEMA_VERSION = 1
RETENTION_DAYS = 7
_RECORD_SUFFIX = ".snapshot.json"
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


class SnapshotArchiveError(RuntimeError):
    """A snapshot could not be safely stored or read."""


class SnapshotStore:
    """Store sealed IMS feed snapshots as independent UTF-8 JSON records."""

    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def save(self, snapshot: ForecastSnapshot) -> Path:
        """Validate and atomically publish one snapshot record."""
        validated = _validated_snapshot(snapshot)
        if not _SAFE_ID.fullmatch(validated.snapshot_id):
            raise SnapshotArchiveError("snapshot_id contains unsafe filename characters")

        final_path = self.directory / f"{validated.snapshot_id}{_RECORD_SUFFIX}"
        temporary_path: Path | None = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.directory,
                prefix=f".{validated.snapshot_id}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(_to_envelope(validated), temporary_file, ensure_ascii=False, indent=2)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, final_path)
        except OSError as error:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not remove temporary snapshot file %s", temporary_path)
            raise SnapshotArchiveError(
                f"Could not save snapshot {validated.snapshot_id}: {error}"
            ) from error

        return final_path

    def find_for_date(
        self,
        feed_type: FeedType,
        target_date: date,
        *,
        as_of: datetime,
    ) -> tuple[ForecastSnapshot, ...]:
        """Return recent snapshots that explicitly contain ``target_date``."""
        _require_aware_as_of(as_of)
        if not isinstance(feed_type, FeedType):
            raise SnapshotArchiveError("feed_type must be a FeedType")
        if type(target_date) is not date:
            raise SnapshotArchiveError("target_date must be a date")

        window_start = as_of - timedelta(days=RETENTION_DAYS)
        matches = []
        for path in self._record_paths():
            try:
                snapshot = _load_record(path)
            except SnapshotArchiveError as error:
                logger.warning("Skipping corrupt snapshot record %s: %s", path, error)
                continue
            if snapshot.feed_type is not feed_type:
                continue
            if target_date not in snapshot.forecast_dates:
                continue
            if snapshot.fetched_at < window_start or snapshot.fetched_at > as_of:
                continue
            matches.append(replace(snapshot, source=SnapshotSource.ARCHIVE))

        matches.sort(key=lambda item: item.snapshot_id)
        matches.sort(key=lambda item: item.fetched_at, reverse=True)
        return tuple(matches)

    def cleanup(self, *, as_of: datetime) -> int:
        """Remove only valid snapshot records outside the retention window."""
        _require_aware_as_of(as_of)
        cutoff = as_of - timedelta(days=RETENTION_DAYS)
        deleted_count = 0
        for path in self._record_paths():
            try:
                snapshot = _load_record(path)
            except SnapshotArchiveError as error:
                logger.warning("Skipping corrupt snapshot record %s: %s", path, error)
                continue
            if snapshot.fetched_at >= cutoff:
                continue
            try:
                path.unlink()
            except OSError as error:
                raise SnapshotArchiveError(
                    f"Could not remove expired snapshot {path}: {error}"
                ) from error
            deleted_count += 1
        return deleted_count

    def _record_paths(self) -> tuple[Path, ...]:
        if not self.directory.exists():
            return ()
        return tuple(self.directory.glob(f"*{_RECORD_SUFFIX}"))


def _to_envelope(snapshot: ForecastSnapshot) -> dict[str, Any]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_id": snapshot.snapshot_id,
        "feed_type": snapshot.feed_type.value,
        "source": snapshot.source.value,
        "fetched_at": snapshot.fetched_at.isoformat(),
        "issued_at": snapshot.issued_at.isoformat(),
        "forecast_dates": [item.isoformat() for item in snapshot.forecast_dates],
        "xml": snapshot.xml,
    }


def _load_record(path: Path) -> ForecastSnapshot:
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SnapshotArchiveError(f"record is not readable UTF-8 JSON: {error}") from error
    if not isinstance(envelope, dict):
        raise SnapshotArchiveError("record must contain a JSON object")

    try:
        if envelope["schema_version"] != SNAPSHOT_SCHEMA_VERSION:
            raise SnapshotArchiveError("unsupported snapshot schema version")
        snapshot = ForecastSnapshot(
            snapshot_id=envelope["snapshot_id"],
            feed_type=FeedType(envelope["feed_type"]),
            source=SnapshotSource(envelope["source"]),
            fetched_at=datetime.fromisoformat(envelope["fetched_at"]),
            issued_at=datetime.fromisoformat(envelope["issued_at"]),
            forecast_dates=tuple(
                date.fromisoformat(item) for item in envelope["forecast_dates"]
            ),
            xml=envelope["xml"],
        )
    except SnapshotArchiveError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise SnapshotArchiveError(f"record fields are invalid: {error}") from error
    return _validated_snapshot(snapshot)


def _validated_snapshot(snapshot: ForecastSnapshot) -> ForecastSnapshot:
    if not isinstance(snapshot, ForecastSnapshot):
        raise SnapshotArchiveError("save requires a ForecastSnapshot")
    try:
        expected = build_snapshot(
            snapshot.xml,
            snapshot.feed_type,
            source=snapshot.source,
            fetched_at=snapshot.fetched_at,
        )
    except (SnapshotValidationError, ValueError) as error:
        raise SnapshotArchiveError(f"snapshot XML is invalid: {error}") from error
    if expected != snapshot:
        raise SnapshotArchiveError("snapshot facts do not match its XML and fetch time")
    return snapshot


def _require_aware_as_of(as_of: datetime) -> None:
    if not isinstance(as_of, datetime) or as_of.tzinfo is None or as_of.utcoffset() is None:
        raise SnapshotArchiveError("as_of must be timezone-aware")
