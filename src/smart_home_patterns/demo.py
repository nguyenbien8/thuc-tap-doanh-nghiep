"""Reproducible synthetic smart-home event log.

The generator simulates two residents with *known* daily routines so that the
discovery step can be checked against a ground truth. The latent activity is
written to the optional ``activity_label`` column, which the pipeline never
uses as a feature – it is only read when scoring the result.

What the demo contains on purpose
---------------------------------
* daily habits (wake up, meals, **taking medicine at ~20:30**, going to bed);
* habits that are sometimes skipped (probability < 1);
* a weekend-only shift for resident_02 (a *second*, rarer pattern);
* an occasional activity (exercise, ~30 % of days) that recurs but is not a habit;
* random short visits to other rooms (noise);
* data-quality defects: duplicated rows, missing values, malformed timestamps,
  inconsistent spelling of room names.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Activity:
    label: str
    room: str
    start_hour: float        # mean start time (decimal hours)
    duration_min: float      # mean duration in minutes
    probability: float = 1.0 # share of days the activity happens
    weekend_shift_h: float = 0.0


# Sensors installed in every room: (sensor_type, event_type, value or (mean, sd))
_ROOM_SENSORS = {
    "bedroom": [("motion", "motion", 1.0), ("light", "reading", (120.0, 20.0)), ("door", "open", 1.0)],
    "kitchen": [("motion", "motion", 1.0), ("door", "open", 1.0), ("temperature", "reading", (23.0, 0.8)),
                ("light", "reading", (320.0, 30.0))],
    "living_room": [("motion", "motion", 1.0), ("power", "on", 1.0), ("light", "reading", (250.0, 30.0))],
    "bathroom": [("motion", "motion", 1.0)],
    "hallway": [("motion", "motion", 1.0)],
}
# Extra sensor that only a specific activity triggers
_ACTIVITY_SENSORS = {"take_medicine": [("pillbox", "open", 1.0)]}

RESIDENTS: dict[str, list[Activity]] = {
    # Retired person, very regular
    "resident_01": [
        Activity("wake_up", "bedroom", 6.75, 15),
        Activity("breakfast", "kitchen", 7.5, 20, 0.95),
        Activity("lunch", "kitchen", 12.0, 30, 0.90),
        Activity("watch_tv", "living_room", 14.0, 60, 0.70),
        Activity("exercise", "living_room", 17.0, 30, 0.30),
        Activity("dinner", "kitchen", 18.5, 35, 0.95),
        Activity("take_medicine", "kitchen", 20.5, 3, 0.85),
        Activity("go_to_bed", "bedroom", 22.5, 10),
    ],
    # Office worker, sleeps in at the weekend, has lunch at work
    "resident_02": [
        Activity("wake_up", "bedroom", 7.75, 12, 1.0, weekend_shift_h=1.5),
        Activity("breakfast", "kitchen", 8.25, 15, 0.85, weekend_shift_h=1.5),
        Activity("dinner", "kitchen", 19.25, 30, 0.90),
        Activity("watch_tv", "living_room", 20.5, 90, 0.80),
        Activity("go_to_bed", "bedroom", 23.25, 10),
    ],
}

START_DATE = datetime(2025, 6, 2)  # a Monday


def _reading(spec, rng: np.random.Generator) -> float:
    if isinstance(spec, tuple):
        return round(float(rng.normal(*spec)), 2)
    return float(spec)


def _session_events(
    resident: str, activity: Activity, start: datetime, duration: float, rng: np.random.Generator
) -> list[dict]:
    """Sensor events of one activity: every sensor of the room fires at the
    start, then motion is re-triggered every ~5 minutes while the person stays."""
    sensors = _ROOM_SENSORS[activity.room] + _ACTIVITY_SENSORS.get(activity.label, [])
    rows = []
    for i, (sensor_type, event_type, spec) in enumerate(sensors):
        rows.append((start + timedelta(minutes=0.5 * i), sensor_type, event_type, _reading(spec, rng)))
    t = 5.0
    while t < duration:
        rows.append((start + timedelta(minutes=t + float(rng.uniform(-1, 1))), "motion", "motion", 1.0))
        t += 5.0
    rows.append((start + timedelta(minutes=duration), "motion", "motion", 1.0))
    return [
        {
            "timestamp": ts.replace(microsecond=0),
            "resident_id": resident,
            "room": activity.room,
            "sensor_type": sensor_type,
            "sensor_id": f"{activity.room}_{sensor_type}",
            "value": value,
            "event_type": event_type,
            "activity_label": activity.label,
        }
        for ts, sensor_type, event_type, value in rows
    ]


def _random_visits(resident: str, day: datetime, rng: np.random.Generator, per_day: int) -> list[dict]:
    """Short, irregular visits (e.g. getting a glass of water) – expected noise."""
    rows = []
    for _ in range(per_day):
        room = str(rng.choice(["bathroom", "hallway", "living_room"]))
        start = day + timedelta(hours=float(rng.uniform(0, 24)))
        for k in range(int(rng.integers(1, 4))):
            rows.append({
                "timestamp": (start + timedelta(minutes=2 * k)).replace(microsecond=0),
                "resident_id": resident,
                "room": room,
                "sensor_type": "motion",
                "sensor_id": f"{room}_motion",
                "value": 1.0,
                "event_type": "motion",
                "activity_label": "random_visit",
            })
    return rows


def _inject_quality_issues(events: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Add the defects a real sensor log typically has (≈1–2 % of rows)."""
    events = events.copy()
    events["timestamp"] = events["timestamp"].astype(str)
    n = len(events)
    missing_value = rng.choice(n, size=n // 100, replace=False)
    events.loc[missing_value, "value"] = np.nan
    bad_time = rng.choice(n, size=n // 400, replace=False)
    events.loc[bad_time, "timestamp"] = "not-a-timestamp"
    messy_room = rng.choice(n, size=n // 50, replace=False)
    events.loc[messy_room, "room"] = " " + events.loc[messy_room, "room"].str.title() + " "
    duplicates = events.sample(frac=0.015, random_state=int(rng.integers(1_000_000)))
    return pd.concat([events, duplicates], ignore_index=True)


def generate_demo_events(days: int = 28, seed: int = 42, noise_per_day: int = 3) -> pd.DataFrame:
    """Generate the demo event log (schema columns + ``activity_label``)."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for d in range(days):
        day = START_DATE + timedelta(days=d)
        weekend = day.weekday() >= 5
        for resident, routine in RESIDENTS.items():
            busy_until = day
            for activity in routine:
                if rng.random() > activity.probability:
                    continue  # the habit is skipped today
                hour = activity.start_hour + (activity.weekend_shift_h if weekend else 0.0)
                start = day + timedelta(hours=hour, minutes=float(rng.normal(0, 10)))
                start = max(start, busy_until + timedelta(minutes=3))  # one activity at a time
                duration = max(1.0, activity.duration_min * float(rng.lognormal(0, 0.2)))
                rows += _session_events(resident, activity, start, duration, rng)
                busy_until = start + timedelta(minutes=duration)
            rows += _random_visits(resident, day, rng, noise_per_day)

    events = _inject_quality_issues(pd.DataFrame(rows), rng)
    # Shuffle to mimic an unordered log collected from many devices
    return events.sample(frac=1, random_state=seed).reset_index(drop=True)


def write_demo(path: str | Path, days: int = 28, seed: int = 42) -> pd.DataFrame:
    """Write demo events to *path* (CSV) and return the DataFrame."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    events = generate_demo_events(days=days, seed=seed)
    events.to_csv(output, index=False)
    return events
