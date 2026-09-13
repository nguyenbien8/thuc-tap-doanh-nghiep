from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp", "resident_id", "room", "sensor_type", "sensor_id", "value", "event_type"
]


@dataclass(frozen=True)
class PreprocessingResult:
    events: pd.DataFrame
    sessions: pd.DataFrame


def validate_schema(events: pd.DataFrame, required_columns: list[str] | None = None) -> None:
    required = required_columns or REQUIRED_COLUMNS
    missing = sorted(set(required) - set(events.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def clean_events(
    events: pd.DataFrame,
    max_missing_fraction: float = 0.40,
    required_columns: list[str] | None = None,
) -> pd.DataFrame:
    validate_schema(events, required_columns)
    clean = events.copy()
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], errors="coerce")
    clean["value"] = pd.to_numeric(clean["value"], errors="coerce")
    missing_fraction = clean.isna().mean(axis=1)
    clean = clean.loc[missing_fraction <= max_missing_fraction].copy()
    clean = clean.dropna(subset=["timestamp", "resident_id", "room", "sensor_type", "sensor_id", "event_type"])
    clean["room"] = clean["room"].astype(str).str.strip().str.lower()
    clean["sensor_type"] = clean["sensor_type"].astype(str).str.strip().str.lower()
    clean["sensor_id"] = clean["sensor_id"].astype(str).str.strip()
    clean["event_type"] = clean["event_type"].astype(str).str.strip().str.lower()
    clean["value"] = clean["value"].fillna(clean.groupby("sensor_type")["value"].transform("median"))
    clean["value"] = clean["value"].fillna(clean["value"].median()).fillna(0.0)
    clean = clean.drop_duplicates().sort_values(["resident_id", "timestamp"]).reset_index(drop=True)
    return clean


def create_sessions(events: pd.DataFrame, inactivity_gap_minutes: int = 30) -> pd.DataFrame:
    if events.empty:
        return events.assign(session_id=pd.Series(dtype="int64"))
    ordered = events.sort_values(["resident_id", "timestamp"]).copy()
    gap = ordered.groupby("resident_id")["timestamp"].diff().dt.total_seconds().div(60).fillna(0)
    ordered["session_id"] = gap.gt(inactivity_gap_minutes).groupby(ordered["resident_id"]).cumsum().astype(int)
    ordered["session_key"] = ordered["resident_id"].astype(str) + "_" + ordered["session_id"].astype(str)
    return ordered.reset_index(drop=True)


def _mode_or_unknown(values: pd.Series) -> str:
    modes = values.dropna().mode()
    return str(modes.iloc[0]) if not modes.empty else "unknown"


def build_session_features(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    rows: list[dict] = []
    for session_key, group in events.groupby("session_key", sort=False):
        start = group["timestamp"].min()
        end = group["timestamp"].max()
        duration = max((end - start).total_seconds() / 60.0, 0.0)
        hour = start.hour + start.minute / 60.0
        row = {
            "session_key": session_key,
            "resident_id": group["resident_id"].iloc[0],
            "start_time": start,
            "end_time": end,
            "duration_minutes": duration,
            "event_count": len(group),
            "unique_rooms": group["room"].nunique(),
            "unique_sensors": group["sensor_id"].nunique(),
            "motion_count": int((group["sensor_type"] == "motion").sum()),
            "door_count": int((group["sensor_type"] == "door").sum()),
            "temperature_mean": group.loc[group["sensor_type"] == "temperature", "value"].mean(),
            "light_mean": group.loc[group["sensor_type"] == "light", "value"].mean(),
            "dominant_room": _mode_or_unknown(group["room"]),
            "dominant_event_type": _mode_or_unknown(group["event_type"]),
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "weekday": int(start.weekday()),
            "weekday_sin": np.sin(2 * np.pi * start.weekday() / 7),
            "weekday_cos": np.cos(2 * np.pi * start.weekday() / 7),
        }
        rows.append(row)
    features = pd.DataFrame(rows)
    numeric = features.select_dtypes(include=np.number).columns
    features[numeric] = features[numeric].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return features


def preprocess(
    events: pd.DataFrame,
    inactivity_gap_minutes: int = 30,
    max_missing_fraction: float = 0.40,
    required_columns: list[str] | None = None,
) -> PreprocessingResult:
    clean = clean_events(
        events,
        max_missing_fraction=max_missing_fraction,
        required_columns=required_columns,
    )
    session_events = create_sessions(clean, inactivity_gap_minutes=inactivity_gap_minutes)
    return PreprocessingResult(events=session_events, sessions=build_session_features(session_events))
