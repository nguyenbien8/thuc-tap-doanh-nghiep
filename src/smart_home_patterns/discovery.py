"""Step 2 – habit discovery with DBSCAN.

Definition of a habit pattern used in this project
--------------------------------------------------
A *habit* is a group of sessions of the **same resident in the same room**
that

1. start at a similar time of day (within ``eps_hours``),
2. have a similar duration, and
3. recur on at least ``min_support`` of the observed days.

Conditions 1–2 are found by DBSCAN (density = "many sessions close to each
other"); condition 3 is checked afterwards on each cluster. Sessions that do
not belong to any dense region get the label ``-1`` (noise / irregular
behaviour).

Distance space
--------------
Each session becomes a 3-D point measured in **hours**:

* ``(x, y)`` – the start time on a circle of circumference 24 h, so the
  straight-line distance between two points is (almost exactly) the number
  of hours between the two start times, and 23:50 is close to 00:10;
* ``z = duration_weight · log2(1 + duration_minutes)`` – doubling the
  duration costs ``duration_weight`` hours of distance.

Because every axis is in hours, ``eps_hours = 0.5`` literally means
"sessions that start within ~30 minutes of each other".
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.neighbors import NearestNeighbors

from .preprocessing import LABEL_COLUMN

HOURS_PER_RADIAN = 24 / (2 * np.pi)
GROUP_COLUMNS = ["resident_id", "dominant_room"]


@dataclass(frozen=True)
class DiscoveryResult:
    sessions: pd.DataFrame      # session table with "cluster" and "is_habit" columns
    profiles: pd.DataFrame      # one row per discovered pattern (cluster)
    metrics: dict               # parameters, counts and quality scores
    k_distances: np.ndarray     # sorted k-NN distances (eps diagnostic)


def habit_feature_matrix(sessions: pd.DataFrame, duration_weight: float = 0.5) -> np.ndarray:
    """Map sessions to the 3-D "hours" space described in the module docstring."""
    angle = 2 * np.pi * sessions["start_hour"].to_numpy(dtype=float) / 24
    duration = sessions["duration_minutes"].to_numpy(dtype=float).clip(min=0)
    return np.column_stack([
        HOURS_PER_RADIAN * np.cos(angle),
        HOURS_PER_RADIAN * np.sin(angle),
        duration_weight * np.log2(1 + duration),
    ])


def observed_days(sessions: pd.DataFrame) -> dict[str, int]:
    """Number of calendar days covered by the data of each resident."""
    dates = pd.to_datetime(sessions["date"])
    span = dates.groupby(sessions["resident_id"]).agg(lambda d: (d.max() - d.min()).days + 1)
    return {str(k): int(v) for k, v in span.items()}


def min_samples_for(days: int, min_samples: int, min_samples_day_ratio: float) -> int:
    """DBSCAN ``min_samples`` for one resident.

    A time slot is dense only if it holds sessions from a meaningful share of
    the observed days, so the requirement grows with the length of the data:
    ``max(min_samples, ceil(ratio · days))``.
    """
    return max(int(min_samples), math.ceil(min_samples_day_ratio * days))


def circular_hour_stats(hours: pd.Series) -> tuple[float, np.ndarray]:
    """Circular mean of clock hours and signed deviations (hours) from it."""
    angle = 2 * np.pi * hours.to_numpy(dtype=float) / 24
    mean_angle = math.atan2(np.sin(angle).mean(), np.cos(angle).mean())
    mean_hour = (mean_angle * HOURS_PER_RADIAN) % 24
    deviation = (hours.to_numpy(dtype=float) - mean_hour + 12) % 24 - 12
    return mean_hour, deviation


def format_hour(hour: float) -> str:
    total = int(round((hour % 24) * 60)) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def _mode(values: pd.Series) -> str:
    modes = values.dropna().mode()
    return str(modes.iloc[0]) if not modes.empty else "unknown"


def build_profiles(
    sessions: pd.DataFrame,
    days_by_resident: dict[str, int],
    min_support: float,
) -> pd.DataFrame:
    """Describe every cluster in human terms: who, where, when, how long, how regular."""
    rows = []
    for cluster_id, group in sessions[sessions["cluster"] >= 0].groupby("cluster"):
        resident = str(group["resident_id"].iloc[0])
        mean_hour, deviation = circular_hour_stats(group["start_hour"])
        low, high = np.quantile(deviation, [0.10, 0.90])
        n_days = group["date"].nunique()
        support = n_days / max(days_by_resident.get(resident, 1), 1)
        row = {
            "cluster": int(cluster_id),
            "resident_id": resident,
            "room": group["dominant_room"].iloc[0],
            "typical_start": format_hour(mean_hour),
            "window_start": format_hour(mean_hour + low),
            "window_end": format_hour(mean_hour + high),
            "start_std_minutes": round(float(np.std(deviation) * 60), 1),
            "median_duration_minutes": round(float(group["duration_minutes"].median()), 1),
            "sessions": int(len(group)),
            "days_present": int(n_days),
            "days_observed": int(days_by_resident.get(resident, 0)),
            "support": round(float(support), 3),
            "is_habit": bool(support >= min_support),
            "sensor_types": _mode(group["sensor_types"]),
            "mean_start_hour": round(float(mean_hour), 4),
        }
        if LABEL_COLUMN in group.columns:
            counts = group[LABEL_COLUMN].value_counts()
            row["dominant_label"] = str(counts.index[0])
            row["label_purity"] = round(float(counts.iloc[0] / len(group)), 3)
        rows.append(row)
    columns = [
        "cluster", "resident_id", "room", "typical_start", "window_start", "window_end",
        "start_std_minutes", "median_duration_minutes", "sessions", "days_present",
        "days_observed", "support", "is_habit", "sensor_types", "mean_start_hour",
    ]
    if LABEL_COLUMN in sessions.columns:
        columns += ["dominant_label", "label_purity"]
    # explicit bool dtype: an empty object column would be read as a column list when filtering
    return pd.DataFrame(rows, columns=columns).astype({"is_habit": bool})


def _relabel_by_time(sessions: pd.DataFrame) -> pd.Series:
    """Renumber clusters 0..n-1 ordered by resident, room and typical start time."""
    clustered = sessions[sessions["cluster"] >= 0]
    if clustered.empty:
        return sessions["cluster"]
    keys = []
    for cluster_id, group in clustered.groupby("cluster"):
        mean_hour, _ = circular_hour_stats(group["start_hour"])
        keys.append((group["resident_id"].iloc[0], group["dominant_room"].iloc[0], mean_hour, cluster_id))
    mapping = {old: new for new, (*_, old) in enumerate(sorted(keys))}
    return sessions["cluster"].map(lambda c: mapping.get(c, -1))


def _within_group_silhouette(matrix: np.ndarray, sessions: pd.DataFrame) -> float | None:
    """Size-weighted silhouette computed inside each (resident, room) group.

    Clusters of different rooms are separated by construction, so a global
    silhouette would be inflated; we only score groups with ≥ 2 clusters.
    """
    scores, weights = [], []
    for _, idx in sessions.groupby(GROUP_COLUMNS).indices.items():
        labels = sessions["cluster"].to_numpy()[idx]
        valid = labels >= 0
        n_clusters = len(set(labels[valid]))
        if n_clusters >= 2 and valid.sum() > n_clusters:
            scores.append(silhouette_score(matrix[idx][valid], labels[valid]))
            weights.append(valid.sum())
    return float(np.average(scores, weights=weights)) if scores else None


def external_scores(sessions: pd.DataFrame) -> dict:
    """Compare clusters with ground-truth labels (only when labels exist).

    Computed on clustered sessions (noise excluded); the truth is
    ``resident_id:activity_label`` because habits are personal.
    """
    if LABEL_COLUMN not in sessions.columns:
        return {}
    clustered = sessions[sessions["cluster"] >= 0]
    if clustered.empty:
        return {"ari": None, "nmi": None, "purity": None}
    truth = clustered["resident_id"].astype(str) + ":" + clustered[LABEL_COLUMN].astype(str)
    purity = clustered.groupby("cluster")[LABEL_COLUMN].agg(lambda s: s.value_counts().iloc[0]).sum() / len(clustered)
    return {
        "ari": float(adjusted_rand_score(truth, clustered["cluster"])),
        "nmi": float(normalized_mutual_info_score(truth, clustered["cluster"])),
        "purity": float(purity),
    }


def discover_patterns(
    sessions: pd.DataFrame,
    eps_hours: float = 0.5,
    min_samples: int = 5,
    min_samples_day_ratio: float = 0.2,
    duration_weight: float = 0.5,
    min_support: float = 0.5,
) -> DiscoveryResult:
    """Run DBSCAN separately for every (resident, room) group.

    Parameters
    ----------
    eps_hours:
        DBSCAN radius in hours of start-time difference.
    min_samples, min_samples_day_ratio:
        Density requirement, see :func:`min_samples_for`.
    duration_weight:
        Hours of distance for a doubling of the session duration.
    min_support:
        Minimum share of observed days a cluster must appear on to be
        reported as a habit (``is_habit``).
    """
    if sessions.empty:
        raise ValueError("No session features available for clustering")

    sessions = sessions.reset_index(drop=True)
    matrix = habit_feature_matrix(sessions, duration_weight)
    days = observed_days(sessions)
    labels = np.full(len(sessions), -1, dtype=int)
    k_distances: list[np.ndarray] = []
    next_id = 0

    for (resident, _room), idx in sessions.groupby(GROUP_COLUMNS).indices.items():
        k = min_samples_for(days[str(resident)], min_samples, min_samples_day_ratio)
        if len(idx) < k:
            continue  # too few sessions in this room to form any pattern → all noise
        points = matrix[idx]
        distances, _ = NearestNeighbors(n_neighbors=k).fit(points).kneighbors(points)
        k_distances.append(distances[:, -1])
        local = DBSCAN(eps=eps_hours, min_samples=k).fit_predict(points)
        found = local >= 0
        labels[idx[found]] = local[found] + next_id
        next_id += int(local.max()) + 1 if found.any() else 0

    result = sessions.copy()
    result["cluster"] = labels
    result["cluster"] = _relabel_by_time(result)
    profiles = build_profiles(result, days, min_support)
    habit_ids = set(profiles.loc[profiles["is_habit"], "cluster"])
    result["is_habit"] = result["cluster"].isin(habit_ids)

    n_clusters = int(result["cluster"].max() + 1)  # ids are 0..n-1, all-noise → 0
    metrics = {
        "n_sessions": int(len(result)),
        "n_clusters": n_clusters,
        "n_habits": int(len(habit_ids)),
        "noise_ratio": float((result["cluster"] == -1).mean()),
        "habit_session_ratio": float(result["is_habit"].mean()),
        "silhouette_within_room": _within_group_silhouette(matrix, result),
        **external_scores(result),
        "parameters": {
            "eps_hours": float(eps_hours),
            "min_samples": int(min_samples),
            "min_samples_day_ratio": float(min_samples_day_ratio),
            "min_samples_by_resident": {
                r: min_samples_for(d, min_samples, min_samples_day_ratio) for r, d in days.items()
            },
            "duration_weight": float(duration_weight),
            "min_support": float(min_support),
            "observed_days": days,
        },
    }
    all_k = np.sort(np.concatenate(k_distances)) if k_distances else np.array([])
    return DiscoveryResult(result, profiles, metrics, all_k)


def save_metrics(metrics: dict, path: str | Path) -> None:
    """Write metrics dict to a JSON file, creating parent directories as needed."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
