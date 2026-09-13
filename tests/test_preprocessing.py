import pandas as pd

from smart_home_patterns.preprocessing import clean_events, create_sessions, preprocess


def sample_events():
    return pd.DataFrame([
        {"timestamp": "2025-01-01 08:00", "resident_id": "r1", "room": " Kitchen ", "sensor_type": "motion", "sensor_id": "m1", "value": 1, "event_type": "MOTION"},
        {"timestamp": "2025-01-01 08:05", "resident_id": "r1", "room": "kitchen", "sensor_type": "temperature", "sensor_id": "t1", "value": None, "event_type": "reading"},
        {"timestamp": "2025-01-01 09:00", "resident_id": "r1", "room": "bedroom", "sensor_type": "door", "sensor_id": "d1", "value": 1, "event_type": "OPEN"},
    ])


def test_clean_events_normalizes_and_removes_missing_required_values():
    clean = clean_events(sample_events())
    assert clean["room"].tolist()[:2] == ["kitchen", "kitchen"]
    assert clean["event_type"].tolist()[0] == "motion"
    assert clean["value"].isna().sum() == 0


def test_create_sessions_splits_after_inactivity_gap():
    sessions = create_sessions(clean_events(sample_events()), inactivity_gap_minutes=30)
    assert sessions["session_key"].nunique() == 2


def test_preprocess_returns_event_and_session_tables():
    result = preprocess(sample_events(), inactivity_gap_minutes=30)
    assert len(result.sessions) == 2
    assert {"hour_sin", "hour_cos", "weekday_sin", "weekday_cos", "event_count"}.issubset(result.sessions.columns)


def test_missing_fraction_removes_rows_before_imputation():
    events = sample_events()
    events.loc[0, ["room", "sensor_type", "sensor_id"]] = None
    clean = clean_events(events, max_missing_fraction=0.20)
    assert len(clean) == 2
