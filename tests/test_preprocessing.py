import pandas as pd

from smart_home_patterns.preprocessing import clean_events, create_sessions, preprocess


def sample_events():
    return pd.DataFrame([
        {"timestamp": "2025-01-01 08:00", "resident_id": "r1", "room": " Kitchen ", "sensor_type": "motion", "sensor_id": "m1", "value": 1, "event_type": "MOTION"},
        {"timestamp": "2025-01-01 08:05", "resident_id": "r1", "room": "kitchen", "sensor_type": "temperature", "sensor_id": "t1", "value": None, "event_type": "reading"},
        {"timestamp": "2025-01-01 09:00", "resident_id": "r1", "room": "bedroom", "sensor_type": "door", "sensor_id": "d1", "value": 1, "event_type": "OPEN"},
    ])


def test_clean_events_normalizes_and_imputes():
    clean = clean_events(sample_events())
    assert clean["room"].tolist()[:2] == ["kitchen", "kitchen"]
    assert clean["event_type"].tolist()[0] == "motion"
    assert clean["value"].isna().sum() == 0


def test_clean_events_drops_bad_timestamps_and_duplicates():
    events = pd.concat([sample_events(), sample_events().iloc[[0]]], ignore_index=True)
    events.loc[2, "timestamp"] = "not-a-timestamp"
    clean = clean_events(events)
    assert len(clean) == 2


def test_missing_fraction_removes_rows_before_imputation():
    events = sample_events()
    events.loc[0, ["room", "sensor_type", "sensor_id"]] = None
    clean = clean_events(events, max_missing_fraction=0.20)
    assert len(clean) == 2


def test_create_sessions_splits_after_inactivity_gap():
    events = clean_events(sample_events())
    events["room"] = "kitchen"
    sessions = create_sessions(events, inactivity_gap_minutes=30)
    assert sessions["session_key"].nunique() == 2


def test_create_sessions_splits_on_room_change():
    events = clean_events(sample_events())
    events.loc[1, "room"] = "bedroom"  # kitchen 08:00 → bedroom 08:05, 09:00 (no gap > 120 min)
    split = create_sessions(events, inactivity_gap_minutes=120, split_on_room_change=True)
    merged = create_sessions(events, inactivity_gap_minutes=120, split_on_room_change=False)
    assert split["session_key"].tolist() == ["r1_0", "r1_1", "r1_1"]
    assert merged["session_key"].nunique() == 1


def test_sessions_are_counted_per_resident():
    events = pd.concat([sample_events(), sample_events().assign(resident_id="r2")], ignore_index=True)
    sessions = create_sessions(clean_events(events))
    assert set(sessions["session_key"]) == {"r1_0", "r1_1", "r2_0", "r2_1"}


def test_preprocess_builds_time_features_and_report():
    result = preprocess(sample_events(), inactivity_gap_minutes=30)
    assert len(result.sessions) == 2
    first = result.sessions.iloc[0]
    assert first["start_hour"] == 8.0
    assert first["duration_minutes"] == 5.0
    assert first["dominant_room"] == "kitchen"
    assert first["sensor_types"] == "motion|temperature"
    assert {"hour_sin", "hour_cos", "date", "event_count"}.issubset(result.sessions.columns)
    assert result.report["raw_events"] == 3 and result.report["sessions_kept"] == 2


def test_min_session_minutes_filters_short_sessions():
    result = preprocess(sample_events(), min_session_minutes=1)
    assert len(result.sessions) == 1  # the one-event bedroom session lasts 0 minutes
    assert result.report["sessions_dropped_short"] == 1


def test_activity_label_is_carried_for_evaluation_only():
    events = sample_events().assign(activity_label=["cook", "cook", "sleep"])
    result = preprocess(events)
    assert result.sessions["activity_label"].tolist() == ["cook", "sleep"]


def test_missing_temperature_uses_dataset_mean_not_zero():
    events = pd.DataFrame([
        {"timestamp": "2025-01-01 08:00", "resident_id": "r1", "room": "kitchen", "sensor_type": "temperature", "sensor_id": "t1", "value": 24.0, "event_type": "reading"},
        {"timestamp": "2025-01-01 12:00", "resident_id": "r1", "room": "kitchen", "sensor_type": "motion", "sensor_id": "m1", "value": 1.0, "event_type": "motion"},
    ])
    sessions = preprocess(events).sessions
    assert sessions["temperature_mean"].tolist() == [24.0, 24.0]


def test_empty_dataframe_edge_cases():
    empty_df = pd.DataFrame(columns=["timestamp", "resident_id", "room", "sensor_type", "sensor_id", "value", "event_type"])
    assert clean_events(empty_df).empty
    sessions = create_sessions(clean_events(empty_df))
    assert sessions.empty and "session_id" in sessions.columns
    prep = preprocess(empty_df)
    assert prep.events.empty and prep.sessions.empty
