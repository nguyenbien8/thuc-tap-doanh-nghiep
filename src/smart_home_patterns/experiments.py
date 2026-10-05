"""Experiments for the report: baseline comparison, ablation and sensitivity.

* **Baseline** – the first version of this project: DBSCAN on all numeric
  session features after StandardScaler, eps = P90 of the k-distance curve.
* **Proposed** – DBSCAN per (resident, room) in the "hours" space
  (:mod:`smart_home_patterns.discovery`).
* **Ablation** – proposed method without splitting sessions on room change.
* **Sensitivity** – proposed method over a grid of eps and min_samples ratio.

Ground-truth labels are only used here, to *score* results; none of the
parameters of the proposed method were tuned on them.
"""
from __future__ import annotations

import copy
import itertools
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from .discovery import circular_hour_stats, discover_patterns, external_scores
from .io import load_config
from .pipeline import load_events, run_preprocessing

BASELINE_FEATURES = [
    "duration_minutes", "event_count", "unique_rooms", "unique_sensors", "motion_count",
    "door_count", "temperature_mean", "light_mean", "hour_sin", "hour_cos",
]


def baseline_clusters(sessions: pd.DataFrame, min_samples: int = 5, quantile: float = 0.90) -> np.ndarray:
    """The original approach, kept for comparison."""
    scaled = StandardScaler().fit_transform(sessions[BASELINE_FEATURES].to_numpy(dtype=float))
    distances, _ = NearestNeighbors(n_neighbors=min_samples).fit(scaled).kneighbors(scaled)
    eps = float(np.quantile(distances[:, -1], quantile))
    return DBSCAN(eps=eps, min_samples=min_samples).fit_predict(scaled)


def time_spread_minutes(sessions: pd.DataFrame) -> float | None:
    """Size-weighted circular std of start times inside clusters (minutes).

    Small = every cluster answers "at what time?" precisely.
    """
    clustered = sessions[sessions["cluster"] >= 0]
    if clustered.empty:
        return None
    spreads = [np.std(circular_hour_stats(g["start_hour"])[1]) * 60 for _, g in clustered.groupby("cluster")]
    sizes = clustered.groupby("cluster").size().to_numpy()
    return float(np.average(spreads, weights=sizes))


def score(sessions: pd.DataFrame) -> dict:
    clustered = sessions["cluster"] >= 0
    return {
        "n_clusters": int(sessions.loc[clustered, "cluster"].nunique()),
        "noise_ratio": float((~clustered).mean()),
        "time_spread_min": time_spread_minutes(sessions),
        **external_scores(sessions),
    }


def _proposed(config: dict, sessions: pd.DataFrame, **overrides) -> dict:
    result = discover_patterns(sessions, **{**config["discovery"], **overrides})
    return {**score(result.sessions), "n_habits": result.metrics["n_habits"]}


def compare_methods(config: dict) -> pd.DataFrame:
    """Baseline vs proposed vs ablation on one dataset."""
    events = load_events(config)
    prep = run_preprocessing(config, events)

    baseline = prep.sessions.assign(cluster=baseline_clusters(prep.sessions))
    rows = [{"method": "Baseline: DBSCAN trên toàn bộ đặc trưng", **score(baseline), "n_habits": None}]

    proposed = _proposed(config, prep.sessions)
    rows.append({"method": "Đề xuất: DBSCAN theo cư dân × phòng", **proposed})

    no_split = copy.deepcopy(config)
    no_split["preprocessing"]["split_on_room_change"] = False
    ablation = _proposed(config, run_preprocessing(no_split, events).sessions)
    rows.append({"method": "Ablation: không tách phiên khi đổi phòng", **ablation})
    return pd.DataFrame(rows).astype({"n_habits": "Int64"})


def sensitivity(config: dict, eps_values=(0.25, 0.5, 0.75, 1.0), ratios=(0.1, 0.2, 0.3)) -> pd.DataFrame:
    sessions = run_preprocessing(config, load_events(config)).sessions
    rows = []
    for eps, ratio in itertools.product(eps_values, ratios):
        result = _proposed(config, sessions, eps_hours=eps, min_samples_day_ratio=ratio)
        rows.append({"eps_hours": eps, "min_samples_day_ratio": ratio, **result})
    return pd.DataFrame(rows)


def _markdown(frame: pd.DataFrame) -> str:
    shown = frame.copy()
    for column in shown.columns:
        if shown[column].dtype.kind == "f":
            shown[column] = shown[column].map(lambda v: "—" if pd.isna(v) else f"{v:.3f}")
    shown = shown.astype(object).where(shown.notna(), "—").astype(str)
    lines = ["| " + " | ".join(shown.columns) + " |", "|" + "---|" * len(shown.columns)]
    lines += ["| " + " | ".join(row) + " |" for row in shown.to_numpy()]
    return "\n".join(lines)


def run_experiments(config_paths: list[str], output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report = [
        "# Thực nghiệm so sánh & phân tích độ nhạy",
        "",
        "> Sinh tự động bởi `smart-home experiments`. Nhãn thật chỉ dùng để chấm điểm.",
        "",
        "Chỉ số: `time_spread_min` = độ lệch chuẩn giờ bắt đầu trong cụm (phút, càng nhỏ càng trả lời chính xác "
        "*“vào lúc nào”*); `ari`, `nmi`, `purity` = mức khớp với nhãn hoạt động thật (tính trên phiên không nhiễu).",
    ]
    for path in config_paths:
        config = load_config(path)
        name = config.get("name", Path(path).stem)
        comparison = compare_methods(config)
        grid = sensitivity(config)
        comparison.to_csv(output / f"{name}_comparison.csv", index=False)
        grid.to_csv(output / f"{name}_sensitivity.csv", index=False)
        report += [
            "", f"## Bộ dữ liệu `{name}`", "",
            "### So sánh phương pháp", "", _markdown(comparison), "",
            "### Độ nhạy theo `eps_hours` và `min_samples_day_ratio`", "", _markdown(grid),
        ]
    (output / "experiments.md").write_text("\n".join(report) + "\n", encoding="utf-8")
