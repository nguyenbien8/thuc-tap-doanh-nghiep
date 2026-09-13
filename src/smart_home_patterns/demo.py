from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd


def generate_demo_events(days: int = 21, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = datetime(2025, 6, 1)
    patterns = [(7.2, "bedroom", "wake_up"), (8.0, "kitchen", "breakfast"), (12.5, "kitchen", "lunch"), (18.5, "kitchen", "dinner"), (22.5, "bedroom", "sleep")]
    rows = []
    for day in range(days):
        for hour, room, activity in patterns:
            center = base + timedelta(days=day, hours=hour) + timedelta(minutes=int(rng.normal(0, 8)))
            for offset, sensor_type, event_type, value in [(0, "motion", "motion", 1), (2, "door", "open", 1), (5, "temperature", "reading", 21 + rng.normal(0, 1)), (8, "light", "reading", 300 + rng.normal(0, 25))]:
                timestamp = center + timedelta(minutes=offset)
                rows.append({"timestamp": timestamp, "resident_id": "resident_01", "room": room, "sensor_type": sensor_type, "sensor_id": f"{room}_{sensor_type}", "value": value, "event_type": event_type, "latent_activity": activity})
    events = pd.DataFrame(rows).drop(columns="latent_activity")
    return events.sample(frac=1, random_state=seed).reset_index(drop=True)


def write_demo(path: str | Path, days: int = 21, seed: int = 42) -> pd.DataFrame:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    events = generate_demo_events(days=days, seed=seed)
    events.to_csv(output, index=False)
    return events
