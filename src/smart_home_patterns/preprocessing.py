"""Step 1 – preprocessing: clean raw sensor events, split them into sessions
(activity episodes) and describe every session with a feature vector.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp", "resident_id", "room", "sensor_type", "sensor_id", "value", "event_type"
]

# Optional ground-truth column. It is carried through preprocessing so that the
# discovered patterns can be *validated* afterwards, but it is never used as a
# clustering feature (the method stays unsupervised).
LABEL_COLUMN = "activity_label"

_STRUCTURAL_COLUMNS = ["timestamp", "resident_id", "room", "sensor_type", "sensor_id", "event_type"]


@dataclass(frozen=True)
class PreprocessingResult:
    events: pd.DataFrame    # cleaned events with session_key
    sessions: pd.DataFrame  # one row per session, feature vector + metadata
    report: dict            # data-quality counters for the report


def validate_schema(events: pd.DataFrame, required_columns: list[str] | None = None) -> None:
    """Raise ValueError if any required column is missing."""
    required = required_columns or REQUIRED_COLUMNS
    missing = sorted(set(required) - set(events.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def clean_events(
    events: pd.DataFrame,
    max_missing_fraction: float = 0.40,
    required_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Validate, coerce types, handle missing values and remove duplicates.

    Steps
    -----
    1. Validate column schema.
    2. Parse ``timestamp`` (invalid → NaT) and coerce ``value`` to numeric (invalid → NaN).
    3. Drop rows where the fraction of missing schema cells exceeds *max_missing_fraction*.
    4. Drop rows with NaN in any structural column (timestamp, resident_id, room,
       sensor_type, sensor_id, event_type).
    5. Normalise category columns: strip whitespace, lowercase.
    6. Fill missing ``value`` with per-sensor-type median, then global median,
       then 0 as last resort.
    7. Remove exact duplicates and sort by resident_id → timestamp.
    """
    validate_schema(events, required_columns)
    clean = events.copy()

    # --- type coercion ---
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], errors="coerce")
    clean["value"] = pd.to_numeric(clean["value"], errors="coerce")

    # --- drop rows with too many missing cells (schema columns only) ---
    missing_fraction = clean[REQUIRED_COLUMNS].isna().mean(axis=1)
    clean = clean.loc[missing_fraction <= max_missing_fraction].copy()

    # --- drop rows missing structural fields ---
    clean = clean.dropna(subset=_STRUCTURAL_COLUMNS)

    # --- normalise categories ---
    clean["resident_id"] = clean["resident_id"].astype(str).str.strip()
    clean["room"] = clean["room"].astype(str).str.strip().str.lower()
    clean["sensor_type"] = clean["sensor_type"].astype(str).str.strip().str.lower()
    clean["sensor_id"] = clean["sensor_id"].astype(str).str.strip()
    clean["event_type"] = clean["event_type"].astype(str).str.strip().str.lower()
    if LABEL_COLUMN in clean.columns:
        clean[LABEL_COLUMN] = clean[LABEL_COLUMN].fillna("unknown").astype(str).str.strip()

    # --- impute value: per-sensor-type median → global median → 0 ---
    clean["value"] = clean["value"].fillna(
        clean.groupby("sensor_type")["value"].transform("median")
    )
    clean["value"] = clean["value"].fillna(clean["value"].median()).fillna(0.0)

    # --- dedup and sort ---
    clean = clean.drop_duplicates().sort_values(["resident_id", "timestamp"], kind="stable")
    return clean.reset_index(drop=True)


def create_sessions(
    events: pd.DataFrame,
    inactivity_gap_minutes: float = 30,
    split_on_room_change: bool = True,
) -> pd.DataFrame:
    """Assign a ``session_id`` and ``session_key`` to every event.

    A new session (activity episode) begins for a resident when

    * the gap to the previous event exceeds *inactivity_gap_minutes*, or
    * (if *split_on_room_change*) the event happens in a different room than
      the previous event of the same resident.

    One session therefore means "one continuous stay of one person in one
    place", which is the unit a habit is built from.
    """
    if events.empty:
        return events.assign(session_id=pd.Series(dtype="int64"), session_key=pd.Series(dtype="object"))
    ordered = events.sort_values(["resident_id", "timestamp"], kind="stable").copy()
    by_resident = ordered.groupby("resident_id", sort=False)
    gap = by_resident["timestamp"].diff().dt.total_seconds().div(60)
    is_new = gap.isna() | gap.gt(inactivity_gap_minutes)
    if split_on_room_change:
        previous_room = by_resident["room"].shift()
        is_new |= previous_room.notna() & ordered["room"].ne(previous_room)
    ordered["session_id"] = is_new.astype(int).groupby(ordered["resident_id"]).cumsum() - 1
    ordered["session_key"] = ordered["resident_id"].astype(str) + "_" + ordered["session_id"].astype(str)
    return ordered.reset_index(drop=True)


def _group_mode(events: pd.DataFrame, column: str) -> pd.Series:
    """Most frequent value of *column* inside every session (ties → first seen)."""
    counts = events.groupby(["session_key", column], sort=False).size()
    top = counts.sort_values(ascending=False, kind="stable").reset_index()
    return top.drop_duplicates("session_key").set_index("session_key")[column]


def build_session_features(events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate every session into one row.

    Time features (used by the pattern discovery step)
    -------------------------------------------------
    - ``start_hour``: start time as a decimal hour (07:30 → 7.5).
    - ``hour_sin``, ``hour_cos``: the start hour placed on the 24-hour circle,
      so 23:55 and 00:05 are close.
    - ``duration_minutes``: time from the first to the last event.

    Context / descriptive features (used for grouping and interpretation)
    ---------------------------------------------------------------------
    - ``dominant_room``, ``dominant_event_type``, ``sensor_types``.
    - ``event_count``, ``unique_rooms``, ``unique_sensors``, ``motion_count``,
      ``door_count``, ``temperature_mean``, ``light_mean`` (sessions without a
      temperature/light reading receive the dataset mean, not a physically
      meaningless 0).
    - ``date``, ``weekday`` (+ cyclic ``weekday_sin``/``weekday_cos``).
    - ``activity_label`` (only if the input has ground truth; evaluation only).
    """
    if events.empty:
        return pd.DataFrame()

    grouped = events.groupby("session_key", sort=False)
    features = grouped.agg(
        resident_id=("resident_id", "first"),
        start_time=("timestamp", "min"),
        end_time=("timestamp", "max"),
        event_count=("timestamp", "size"),
        unique_rooms=("room", "nunique"),
        unique_sensors=("sensor_id", "nunique"),
    )
    features["duration_minutes"] = (
        (features["end_time"] - features["start_time"]).dt.total_seconds().div(60).clip(lower=0)
    )

    by_type = (
        events.groupby(["session_key", "sensor_type"]).size()
        .unstack(fill_value=0).reindex(features.index, fill_value=0)
    )
    for sensor_type in ("motion", "door"):
        features[f"{sensor_type}_count"] = by_type[sensor_type] if sensor_type in by_type.columns else 0

    for sensor_type, name in (("temperature", "temperature_mean"), ("light", "light_mean")):
        readings = events.loc[events["sensor_type"] == sensor_type]
        global_mean = float(readings["value"].mean()) if not readings.empty else 0.0
        features[name] = readings.groupby("session_key")["value"].mean().reindex(features.index).fillna(global_mean)

    features["dominant_room"] = _group_mode(events, "room")
    features["dominant_event_type"] = _group_mode(events, "event_type")
    features["sensor_types"] = grouped["sensor_type"].agg(lambda s: "|".join(sorted(s.unique())))
    if LABEL_COLUMN in events.columns:
        features[LABEL_COLUMN] = _group_mode(events, LABEL_COLUMN)

    start = features["start_time"]
    features["start_hour"] = start.dt.hour + start.dt.minute / 60 + start.dt.second / 3600
    features["hour_sin"] = np.sin(2 * np.pi * features["start_hour"] / 24)
    features["hour_cos"] = np.cos(2 * np.pi * features["start_hour"] / 24)
    features["date"] = start.dt.strftime("%Y-%m-%d")
    features["weekday"] = start.dt.weekday
    features["weekday_sin"] = np.sin(2 * np.pi * features["weekday"] / 7)
    features["weekday_cos"] = np.cos(2 * np.pi * features["weekday"] / 7)

    return features.reset_index()


def preprocess(
    events: pd.DataFrame,
    inactivity_gap_minutes: float = 30,
    max_missing_fraction: float = 0.40,
    required_columns: list[str] | None = None,
    split_on_room_change: bool = True,
    min_session_minutes: float = 0.0,
) -> PreprocessingResult:
    """Full step 1: clean → sessionize → feature extraction → filter.

    Sessions shorter than *min_session_minutes* (e.g. walking through a
    corridor) are dropped from the session table; their events stay in the
    cleaned event log.
    """
    clean = clean_events(
        events,
        max_missing_fraction=max_missing_fraction,
        required_columns=required_columns,
    )
    session_events = create_sessions(
        clean,
        inactivity_gap_minutes=inactivity_gap_minutes,
        split_on_room_change=split_on_room_change,
    )
    sessions = build_session_features(session_events)
    n_all_sessions = len(sessions)
    if min_session_minutes > 0 and not sessions.empty:
        sessions = sessions.loc[sessions["duration_minutes"] >= min_session_minutes].reset_index(drop=True)
    report = {
        "raw_events": int(len(events)),
        "clean_events": int(len(clean)),
        "dropped_events": int(len(events) - len(clean)),
        "sessions_total": int(n_all_sessions),
        "sessions_kept": int(len(sessions)),
        "sessions_dropped_short": int(n_all_sessions - len(sessions)),
    }
    return PreprocessingResult(events=session_events, sessions=sessions, report=report)
