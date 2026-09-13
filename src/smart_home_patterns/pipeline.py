from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from .discovery import discover_patterns, k_distance_values, save_metrics
from .io import read_events, write_frame
from .preprocessing import preprocess


def run_pipeline(config: dict, input_path: str | Path) -> dict:
    data_cfg, prep_cfg, cluster_cfg, report_cfg = config["data"], config["preprocessing"], config["clustering"], config["report"]
    result = preprocess(
        read_events(input_path),
        data_cfg["inactivity_gap_minutes"],
        prep_cfg["max_missing_fraction"],
        prep_cfg["required_columns"],
    )
    write_frame(result.events, data_cfg["events_path"])
    discovery = discover_patterns(result.sessions, cluster_cfg["min_samples"], eps_quantile=cluster_cfg["eps_quantile"], pca_components=cluster_cfg["pca_components"])
    write_frame(discovery.sessions, data_cfg["processed_path"])
    write_frame(discovery.profiles, report_cfg["profiles_path"])
    save_metrics(discovery.metrics, report_cfg["metrics_path"])
    output_dir = Path(report_cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 6))
    sns.scatterplot(data=discovery.embedding, x="pca_1", y="pca_2", hue="cluster", palette="tab10", s=70)
    plt.title("DBSCAN discovery of recurring smart-home activities")
    plt.tight_layout()
    plt.savefig(output_dir / "activity_clusters_pca.png", dpi=160)
    plt.close()
    feature_matrix = discovery.sessions[discovery.metrics["feature_columns"]].fillna(0.0).to_numpy(dtype=float)
    distances = k_distance_values(feature_matrix, cluster_cfg["min_samples"])
    if len(distances):
        plt.figure(figsize=(9, 5))
        plt.plot(np.arange(1, len(distances) + 1), distances)
        plt.axhline(discovery.metrics["eps"], color="crimson", linestyle="--", label=f"eps={discovery.metrics['eps']:.3f}")
        plt.xlabel("Sessions sorted by k-distance")
        plt.ylabel("Distance to kth neighbor")
        plt.title("K-distance diagnostic for DBSCAN eps")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "k_distance_diagnostic.png", dpi=160)
        plt.close()
    return discovery.metrics
