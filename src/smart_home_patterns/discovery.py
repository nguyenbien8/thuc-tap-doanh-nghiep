from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class DiscoveryResult:
    sessions: pd.DataFrame
    metrics: dict
    profiles: pd.DataFrame
    embedding: pd.DataFrame


def select_feature_columns(sessions: pd.DataFrame) -> list[str]:
    excluded = {
        "session_key", "resident_id", "start_time", "end_time",
        "dominant_room", "dominant_event_type", "weekday",
        "weekday_sin", "weekday_cos",
    }
    return [column for column in sessions.select_dtypes(include=np.number).columns if column not in excluded]


def estimate_eps(features: np.ndarray, min_samples: int = 5, quantile: float = 0.90) -> float:
    if len(features) <= min_samples:
        return 0.8
    neighbors = NearestNeighbors(n_neighbors=min_samples).fit(features)
    distances, _ = neighbors.kneighbors(features)
    return float(np.quantile(np.sort(distances[:, -1]), quantile))


def k_distance_values(features: np.ndarray, min_samples: int = 5) -> np.ndarray:
    """Return sorted k-neighbor distances for an auditable eps diagnostic."""
    if len(features) <= min_samples:
        return np.array([])
    neighbors = NearestNeighbors(n_neighbors=min_samples).fit(features)
    distances, _ = neighbors.kneighbors(features)
    return np.sort(distances[:, -1])


def _metrics(features: np.ndarray, labels: np.ndarray) -> dict:
    valid = labels >= 0
    cluster_count = len(set(labels[valid])) if valid.any() else 0
    metrics = {
        "n_sessions": int(len(labels)),
        "n_clusters": int(cluster_count),
        "noise_ratio": float(np.mean(labels == -1)) if len(labels) else 0.0,
    }
    if cluster_count >= 2 and valid.sum() > cluster_count:
        metrics["silhouette_score"] = float(silhouette_score(features[valid], labels[valid]))
        metrics["davies_bouldin_score"] = float(davies_bouldin_score(features[valid], labels[valid]))
        metrics["calinski_harabasz_score"] = float(calinski_harabasz_score(features[valid], labels[valid]))
    else:
        metrics.update({"silhouette_score": None, "davies_bouldin_score": None, "calinski_harabasz_score": None})
    return metrics


def build_profiles(sessions: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    clustered = sessions[sessions["cluster"] >= 0]
    if clustered.empty:
        return pd.DataFrame(columns=["cluster", "sessions", "share", "typical_room", "typical_event"] + feature_columns)
    profiles = clustered.groupby("cluster")[feature_columns].mean().reset_index()
    counts = clustered.groupby("cluster").size().rename("sessions")
    profiles = profiles.merge(counts, on="cluster")
    profiles["share"] = profiles["sessions"] / len(sessions)
    room = clustered.groupby("cluster")["dominant_room"].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "unknown")
    event = clustered.groupby("cluster")["dominant_event_type"].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "unknown")
    profiles["typical_room"] = profiles["cluster"].map(room)
    profiles["typical_event"] = profiles["cluster"].map(event)
    return profiles.sort_values("cluster").reset_index(drop=True)


def discover_patterns(sessions: pd.DataFrame, min_samples: int = 5, eps: float | None = None, eps_quantile: float = 0.90, pca_components: int = 2) -> DiscoveryResult:
    if sessions.empty:
        raise ValueError("No session features available for clustering")
    feature_columns = select_feature_columns(sessions)
    if not feature_columns:
        raise ValueError("No numeric features available for clustering")
    matrix = sessions[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy(dtype=float)
    scaled = StandardScaler().fit_transform(matrix)
    chosen_eps = eps if eps is not None else estimate_eps(scaled, min_samples=min_samples, quantile=eps_quantile)
    labels = DBSCAN(eps=chosen_eps, min_samples=min_samples).fit_predict(scaled)
    result = sessions.copy()
    result["cluster"] = labels
    components = min(pca_components, scaled.shape[1], len(result))
    embedding_values = PCA(n_components=max(1, components), random_state=42).fit_transform(scaled)
    embedding = pd.DataFrame({"session_key": result["session_key"], "cluster": labels, "pca_1": embedding_values[:, 0]})
    embedding["pca_2"] = embedding_values[:, 1] if embedding_values.shape[1] > 1 else 0.0
    metrics = _metrics(scaled, labels) | {"eps": float(chosen_eps), "min_samples": int(min_samples), "feature_columns": feature_columns}
    return DiscoveryResult(result, metrics, build_profiles(result, feature_columns), embedding)


def save_metrics(metrics: dict, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
