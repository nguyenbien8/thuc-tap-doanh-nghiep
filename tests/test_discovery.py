import pandas as pd

from smart_home_patterns.discovery import discover_patterns, k_distance_values


def test_discovery_returns_labels_metrics_and_profiles():
    sessions = pd.DataFrame({
        "session_key": [f"s{i}" for i in range(12)], "resident_id": ["r1"] * 12,
        "start_time": pd.date_range("2025-01-01", periods=12, freq="h"), "end_time": pd.date_range("2025-01-01", periods=12, freq="h"),
        "duration_minutes": [10, 11, 9, 10, 50, 52, 49, 51, 10, 11, 9, 10],
        "event_count": [4, 4, 5, 4, 10, 11, 9, 10, 4, 4, 5, 4], "unique_rooms": [1] * 12,
        "unique_sensors": [2] * 12, "motion_count": [1] * 12, "door_count": [1] * 12,
        "temperature_mean": [21.0] * 12, "light_mean": [300.0] * 12,
        "dominant_room": ["kitchen"] * 12, "dominant_event_type": ["motion"] * 12,
        "hour_sin": [0.0] * 12, "hour_cos": [1.0] * 12, "weekday": [1] * 12,
    })
    result = discover_patterns(sessions, min_samples=2, eps=0.8)
    assert "cluster" in result.sessions
    assert result.metrics["n_sessions"] == 12
    assert "noise_ratio" in result.metrics


def test_k_distance_values_are_sorted_for_eps_diagnostics():
    sessions = pd.DataFrame({"x": [0.0, 0.1, 0.2, 4.0, 4.1, 4.2]})
    distances = k_distance_values(sessions.to_numpy(), min_samples=2)
    assert len(distances) == 6
    assert (distances[:-1] <= distances[1:]).all()
