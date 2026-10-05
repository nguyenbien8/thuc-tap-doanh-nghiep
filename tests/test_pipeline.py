import json
from pathlib import Path

from smart_home_patterns.demo import generate_demo_events
from smart_home_patterns.pipeline import run_pipeline
from smart_home_patterns.strands_adapter import load_strands

REQUIRED = ["timestamp", "resident_id", "room", "sensor_type", "sensor_id", "value", "event_type"]


def make_config(tmp_path: Path, raw_path: Path) -> dict:
    return {
        "name": "test",
        "data": {"source": "csv", "raw_path": str(raw_path)},
        "preprocessing": {
            "required_columns": REQUIRED,
            "max_missing_fraction": 0.40,
            "inactivity_gap_minutes": 30,
            "split_on_room_change": True,
            "min_session_minutes": 0,
        },
        "discovery": {
            "eps_hours": 0.5, "min_samples": 5, "min_samples_day_ratio": 0.2,
            "duration_weight": 0.5, "min_support": 0.5,
        },
        "output": {"processed_dir": str(tmp_path / "processed"), "results_dir": str(tmp_path / "results")},
    }


def test_end_to_end_pipeline_recovers_demo_habits(tmp_path: Path):
    raw_path = tmp_path / "raw.csv"
    generate_demo_events(days=14, seed=7).to_csv(raw_path, index=False)

    metrics = run_pipeline(make_config(tmp_path, raw_path))

    results = tmp_path / "results"
    for name in ("metrics.json", "habits.csv", "habit_report.md",
                 "figures/habit_timeline.png", "figures/k_distance.png", "figures/actogram.png",
                 "figures/label_matrix.png"):
        assert (results / name).exists(), name
    assert (tmp_path / "processed" / "sessions.csv").exists()

    saved = json.loads((results / "metrics.json").read_text(encoding="utf-8"))
    assert saved["n_sessions"] == metrics["n_sessions"] > 0
    assert saved["preprocessing"]["dropped_events"] > 0      # the demo contains defects
    assert metrics["n_habits"] >= 8
    assert metrics["purity"] > 0.95


def test_demo_is_reproducible():
    assert generate_demo_events(days=3, seed=1).equals(generate_demo_events(days=3, seed=1))


def test_strands_adapter_reads_minute_files(tmp_path: Path):
    folder = tmp_path / "aruba"
    folder.mkdir()
    (folder / "location.names").write_text("Master Bedroom\nKitchen\nSecond Bathroom\n", encoding="utf-8")
    (folder / "activity.names").write_text("None\nSleeping\nMeal_Preparation\n", encoding="utf-8")
    (folder / "location.min").write_text("1\n1\n2\n3\n", encoding="utf-8")
    (folder / "activity.min").write_text("1\n1\n2\n7\n", encoding="utf-8")

    events = load_strands(folder, start_date="2020-01-01", location_overrides={3: "Outside"})

    assert list(events.columns) == REQUIRED + ["activity_label"]
    assert events["room"].tolist() == ["master_bedroom", "master_bedroom", "kitchen", "outside"]
    assert events["activity_label"].tolist() == ["Sleeping", "Sleeping", "Meal_Preparation", "unknown_7"]
    assert str(events["timestamp"].iloc[3]) == "2020-01-01 00:03:00"
    assert (events["resident_id"] == "aruba").all()
