import numpy as np
import pandas as pd

from smart_home_patterns.discovery import (
    circular_hour_stats,
    discover_patterns,
    format_hour,
    habit_feature_matrix,
)


def make_sessions(specs, days=20, seed=0):
    """specs: list of (room, mean_hour, duration_min, probability)."""
    rng = np.random.default_rng(seed)
    rows = []
    for day in range(days):
        date = (pd.Timestamp("2025-01-01") + pd.Timedelta(days=day)).strftime("%Y-%m-%d")
        for room, hour, duration, probability in specs:
            if rng.random() < probability:
                rows.append({
                    "session_key": f"r1_{len(rows)}", "resident_id": "r1", "dominant_room": room,
                    "start_hour": (hour + rng.normal(0, 0.1)) % 24, "duration_minutes": duration,
                    "date": date, "sensor_types": "motion",
                })
    return pd.DataFrame(rows)


def test_feature_space_is_measured_in_hours():
    sessions = pd.DataFrame({"start_hour": [8.0, 8.5, 23.9, 0.1], "duration_minutes": [10, 10, 10, 10]})
    m = habit_feature_matrix(sessions)
    assert abs(np.linalg.norm(m[0] - m[1]) - 0.5) < 0.01          # 30 minutes apart
    assert np.linalg.norm(m[2] - m[3]) < 0.25                      # across midnight: 12 minutes apart


def test_circular_mean_handles_midnight():
    mean, deviation = circular_hour_stats(pd.Series([23.5, 0.5]))
    assert format_hour(mean) == "00:00"
    assert np.allclose(np.abs(deviation), 0.5)


def test_discovers_daily_habits_and_separates_rare_pattern():
    sessions = make_sessions([
        ("kitchen", 8.0, 20, 1.0),     # daily breakfast
        ("kitchen", 20.5, 3, 0.9),     # medicine, sometimes skipped
        ("kitchen", 15.0, 10, 0.3),    # occasional snack
    ], days=30)
    result = discover_patterns(sessions, eps_hours=0.5, min_samples=3, min_samples_day_ratio=0.1)
    profiles = result.profiles.set_index("typical_start")
    habits = result.profiles[result.profiles["is_habit"]]
    assert len(habits) == 2
    assert set(habits["room"]) == {"kitchen"}
    starts = sorted(habits["mean_start_hour"].round())
    assert starts == [8.0, 20.0] or starts == [8.0, 21.0]
    snack = result.profiles[~result.profiles["is_habit"]]
    assert len(snack) == 1 and snack["support"].iloc[0] < 0.5
    assert result.metrics["n_habits"] == 2
    assert profiles["days_observed"].eq(30).all()


def test_rooms_are_clustered_separately():
    sessions = make_sessions([("kitchen", 8.0, 20, 1.0), ("bedroom", 8.0, 20, 1.0)])
    result = discover_patterns(sessions, min_samples=3, min_samples_day_ratio=0.1)
    assert result.metrics["n_clusters"] == 2
    assert set(result.profiles["room"]) == {"kitchen", "bedroom"}


def test_isolated_sessions_are_noise():
    sessions = make_sessions([("kitchen", 8.0, 20, 1.0)])
    lonely = sessions.iloc[[0]].assign(session_key="lonely", start_hour=3.0)
    result = discover_patterns(pd.concat([sessions, lonely], ignore_index=True), min_samples=3)
    assert result.sessions.loc[result.sessions["session_key"] == "lonely", "cluster"].iloc[0] == -1


def test_all_noise_returns_empty_but_typed_profiles():
    sessions = make_sessions([("kitchen", 8.0, 20, 1.0)], days=3)
    result = discover_patterns(sessions, min_samples=10)
    assert result.metrics["n_clusters"] == 0
    assert result.profiles.empty
    assert result.profiles[result.profiles["is_habit"]].columns.tolist() == result.profiles.columns.tolist()


def test_external_scores_use_labels_when_present():
    sessions = make_sessions([("kitchen", 8.0, 20, 1.0), ("kitchen", 19.0, 30, 1.0)])
    sessions["activity_label"] = np.where(sessions["start_hour"] < 12, "breakfast", "dinner")
    result = discover_patterns(sessions, min_samples=3)
    assert result.metrics["purity"] == 1.0
    assert result.metrics["ari"] == 1.0
    assert set(result.profiles["dominant_label"]) == {"breakfast", "dinner"}
