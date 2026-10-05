"""End-to-end run: load → preprocess (step 1) → discover habits (step 2) → report."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from .discovery import DiscoveryResult, discover_patterns, save_metrics
from .io import read_events, write_frame
from .plots import plot_actogram, plot_habit_timeline, plot_k_distance, plot_label_matrix
from .preprocessing import LABEL_COLUMN, PreprocessingResult, preprocess
from .strands_adapter import load_strands


def load_events(config: dict, input_path: str | Path | None = None) -> pd.DataFrame:
    """Read the raw event log described by ``config['data']``."""
    data_cfg = config["data"]
    if data_cfg.get("source", "csv") == "strands" and input_path is None:
        options = dict(data_cfg["strands"])
        return load_strands(options.pop("folder"), **options)
    return read_events(input_path or data_cfg["raw_path"])


def run_preprocessing(config: dict, events: pd.DataFrame) -> PreprocessingResult:
    prep_cfg = config["preprocessing"]
    return preprocess(
        events,
        inactivity_gap_minutes=prep_cfg["inactivity_gap_minutes"],
        max_missing_fraction=prep_cfg["max_missing_fraction"],
        required_columns=prep_cfg["required_columns"],
        split_on_room_change=prep_cfg.get("split_on_room_change", True),
        min_session_minutes=prep_cfg.get("min_session_minutes", 0.0),
    )


def run_discovery(config: dict, sessions: pd.DataFrame) -> DiscoveryResult:
    return discover_patterns(sessions, **config["discovery"])


def write_habit_report(name: str, prep: PreprocessingResult, discovery: DiscoveryResult, path: Path) -> None:
    """Human-readable summary of the run (Markdown, Vietnamese)."""
    m, p = discovery.metrics, discovery.metrics["parameters"]
    profiles = discovery.profiles
    has_labels = "dominant_label" in profiles.columns

    def table(rows: pd.DataFrame) -> list[str]:
        head = "| Cụm | Cư dân | Phòng | Giờ điển hình | Khung 80% | Thời lượng TV | Số ngày | Tần suất |"
        sep = "|---:|---|---|:---:|:---:|---:|---:|---:|"
        if has_labels:
            head += " Nhãn thật chiếm đa số (độ thuần) |"
            sep += "---|"
        lines = [head, sep]
        for r in rows.itertuples():
            line = (f"| C{r.cluster} | {r.resident_id} | {r.room} | **{r.typical_start}** | "
                    f"{r.window_start}–{r.window_end} | {r.median_duration_minutes:g} phút | "
                    f"{r.days_present}/{r.days_observed} | {r.support:.0%} |")
            if has_labels:
                line += f" {r.dominant_label} ({r.label_purity:.0%}) |"
            lines.append(line)
        return lines

    habits = profiles[profiles["is_habit"]]
    others = profiles[~profiles["is_habit"]]
    fmt = lambda v: "—" if v is None else f"{v:.3f}"  # noqa: E731
    lines = [
        f"# Kết quả thực nghiệm: `{name}`",
        "",
        "> File này được sinh tự động bởi `smart-home run`. Không sửa tay.",
        "",
        "## Bước 1 – Tiền xử lý",
        "",
        f"- Sự kiện thô: **{prep.report['raw_events']:,}** → sau làm sạch: **{prep.report['clean_events']:,}** "
        f"(loại {prep.report['dropped_events']:,}).",
        f"- Phiên tạo được: **{prep.report['sessions_total']:,}**; giữ lại **{prep.report['sessions_kept']:,}** "
        f"(loại {prep.report['sessions_dropped_short']:,} phiên quá ngắn).",
        "",
        "## Bước 2 – Tìm mẫu thói quen (DBSCAN theo cư dân × phòng)",
        "",
        f"- Tham số: `eps = {p['eps_hours']} giờ`, `min_samples = max({p['min_samples']}, "
        f"⌈{p['min_samples_day_ratio']} × số ngày⌉)` = {p['min_samples_by_resident']}, "
        f"`duration_weight = {p['duration_weight']}`, ngưỡng thói quen `min_support = {p['min_support']:.0%}` số ngày.",
        f"- Số cụm: **{m['n_clusters']}**, trong đó **{m['n_habits']} thói quen**; "
        f"tỷ lệ nhiễu: **{m['noise_ratio']:.1%}** số phiên.",
        f"- Silhouette trong từng phòng: {fmt(m['silhouette_within_room'])}.",
    ]
    if "ari" in m:
        lines.append(
            f"- Đối chiếu nhãn thật (không dùng khi huấn luyện): ARI = {fmt(m['ari'])}, "
            f"NMI = {fmt(m['nmi'])}, độ thuần = {fmt(m['purity'])}."
        )
    lines += ["", "### Thói quen tìm được", ""]
    lines += table(habits) if not habits.empty else ["_Không có cụm nào đạt ngưỡng thói quen._"]
    lines += ["", "### Mẫu lặp lại nhưng chưa đủ thường xuyên", ""]
    lines += table(others) if not others.empty else ["_Không có._"]
    lines += [
        "",
        "Ghi chú: *Khung 80%* là khoảng giữa phân vị 10% và 90% của giờ bắt đầu; "
        "*Tần suất* = số ngày có mẫu / số ngày quan sát.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_pipeline(config: dict, input_path: str | Path | None = None) -> dict:
    """Execute the whole pipeline and write every artefact. Returns metrics."""
    name = config.get("name", "experiment")
    out_cfg = config["output"]
    processed_dir = Path(out_cfg["processed_dir"])
    results_dir = Path(out_cfg["results_dir"])
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: preprocessing ───────────────────────────────────────────────
    prep = run_preprocessing(config, load_events(config, input_path))
    write_frame(prep.events, processed_dir / "clean_events.csv")

    # ── Step 2: habit discovery ─────────────────────────────────────────────
    discovery = run_discovery(config, prep.sessions)
    write_frame(discovery.sessions, processed_dir / "sessions.csv")
    write_frame(discovery.profiles, results_dir / "habits.csv")
    metrics = {"dataset": name, "preprocessing": prep.report, **discovery.metrics}
    save_metrics(metrics, results_dir / "metrics.json")
    write_habit_report(name, prep, discovery, results_dir / "habit_report.md")

    # ── Figures ─────────────────────────────────────────────────────────────
    title = config.get("title", name)
    plot_habit_timeline(discovery.sessions, discovery.profiles, figures_dir / "habit_timeline.png",
                        f"Các mẫu tìm được theo giờ trong ngày – {title}")
    plot_k_distance(discovery.k_distances, config["discovery"]["eps_hours"], figures_dir / "k_distance.png")
    plot_actogram(discovery.sessions, figures_dir / "actogram.png", f"Nhật ký vị trí theo ngày – {title}")
    if LABEL_COLUMN in discovery.sessions.columns:
        plot_label_matrix(discovery.sessions, discovery.profiles, figures_dir / "label_matrix.png")
    return metrics
