"""Figures for the report. All text is Vietnamese; colours follow one palette:
blue = habit, orange = recurring but not a habit, grey = noise."""
from __future__ import annotations

from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .preprocessing import LABEL_COLUMN  # noqa: E402

HABIT = "#2a78d6"
OCCASIONAL = "#eb6834"
NOISE = "#9a9a96"
INK = "#0b0b0b"
INK_MUTED = "#52514e"
GRID = "#e4e3df"
ROOM_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_MUTED,
    "axes.titlecolor": INK,
    "axes.titleweight": "bold",
    "axes.titlesize": 12,
    "axes.titlelocation": "left",
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def _hour_axis(ax) -> None:
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 3)])
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _row_label(resident: str, room: str, multi_resident: bool) -> str:
    return f"{resident} · {room}" if multi_resident else room


def plot_habit_timeline(sessions: pd.DataFrame, profiles: pd.DataFrame, path: Path, title: str) -> None:
    """One row per (resident, room); each dot is a session at its start time."""
    multi = sessions["resident_id"].nunique() > 1
    groups = (
        sessions.groupby(["resident_id", "dominant_room"]).size()
        .reset_index(name="n").sort_values(["resident_id", "dominant_room"], ascending=[True, False])
    )
    fig, ax = plt.subplots(figsize=(11, 0.75 * len(groups) + 1.6))
    rng = np.random.default_rng(0)
    habit_ids = set(profiles.loc[profiles["is_habit"], "cluster"])

    for row, (_, g) in enumerate(groups.iterrows()):
        part = sessions[(sessions["resident_id"] == g["resident_id"]) & (sessions["dominant_room"] == g["dominant_room"])]
        y = row + rng.uniform(-0.22, 0.22, len(part))
        colors = np.where(part["cluster"] < 0, NOISE, np.where(part["cluster"].isin(habit_ids), HABIT, OCCASIONAL))
        sizes = np.where(part["cluster"] < 0, 10, 16)
        ax.scatter(part["start_hour"], y, c=colors, s=sizes, alpha=0.75, linewidths=0)

        own = profiles[(profiles["resident_id"] == g["resident_id"]) & (profiles["room"] == g["dominant_room"])]
        last_label_x = -99.0
        for _, p in own.sort_values("mean_start_hour").iterrows():
            color = HABIT if p["is_habit"] else OCCASIONAL
            low = p["mean_start_hour"] + _signed_offset(p["window_start"], p["mean_start_hour"])
            high = p["mean_start_hour"] + _signed_offset(p["window_end"], p["mean_start_hour"])
            for a, b in _wrap_span(low, high):
                ax.fill_between([a, b], row - 0.36, row + 0.36, color=color, alpha=0.10, linewidth=0)
            x = p["mean_start_hour"] % 24
            below = x - last_label_x < 1.8  # two labels would collide: put this one under the row
            ax.text(x, row - 0.40 if below else row + 0.40, f"{p['typical_start']} · {p['support']:.0%}",
                    ha="center", va="top" if below else "bottom", fontsize=8, color=INK)
            last_label_x = -99.0 if below else x

    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([_row_label(r, m, multi) for r, m in zip(groups["resident_id"], groups["dominant_room"])])
    ax.set_ylim(-0.75, len(groups) - 0.2)
    _hour_axis(ax)
    ax.set_xlabel("Giờ bắt đầu phiên")
    ax.set_title(title)
    fig.legend(
        handles=[Patch(color=HABIT, label="Thói quen (≥ ngưỡng số ngày)"),
                 Patch(color=OCCASIONAL, label="Mẫu lặp lại, chưa đủ thường xuyên"),
                 Patch(color=NOISE, label="Nhiễu (DBSCAN = −1)")],
        loc="lower center", ncol=3, frameon=False,
    )
    fig.tight_layout(rect=(0, 0.6 / fig.get_figheight(), 1, 1))
    fig.savefig(path, dpi=170)
    plt.close(fig)


def _signed_offset(clock: str, mean_hour: float) -> float:
    h, m = map(int, clock.split(":"))
    return ((h + m / 60) - mean_hour + 12) % 24 - 12


def _wrap_span(low: float, high: float) -> list[tuple[float, float]]:
    low, high = low % 24, high % 24
    return [(low, high)] if low <= high else [(low, 24), (0, high)]


def plot_k_distance(k_distances: np.ndarray, eps: float, path: Path) -> None:
    """Sorted distance to the k-th neighbour, with the chosen eps."""
    if not len(k_distances):
        return
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(np.arange(1, len(k_distances) + 1), k_distances, color=HABIT, linewidth=2)
    ax.axhline(eps, color=OCCASIONAL, linestyle="--", linewidth=1.5)
    share = float(np.mean(k_distances <= eps))
    ax.text(len(k_distances) * 0.02, eps, f"eps = {eps:g} giờ  ({share:.0%} phiên là điểm lõi)",
            va="bottom", color=INK, fontsize=9)
    ax.set_ylim(0, min(float(k_distances.max()) * 1.05, max(eps * 6, 1.0)))
    ax.set_xlabel("Các phiên, sắp xếp theo khoảng cách tăng dần")
    ax.set_ylabel("Khoảng cách tới láng giềng thứ k (giờ)")
    ax.set_title("Biểu đồ k-distance: cơ sở chọn eps")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def plot_actogram(sessions: pd.DataFrame, path: Path, title: str, max_rooms: int = 5) -> None:
    """Day × time-of-day chart: where each resident was, day after day."""
    residents = sorted(sessions["resident_id"].unique())
    weight = sessions.groupby("dominant_room")["duration_minutes"].sum() + sessions.groupby("dominant_room").size()
    top_rooms = list(weight.sort_values(ascending=False).index[:max_rooms])
    color_of = {room: ROOM_COLORS[i] for i, room in enumerate(top_rooms)}

    start_day = pd.to_datetime(sessions["date"]).min()
    n_days = int((pd.to_datetime(sessions["date"]).max() - start_day).days) + 1
    fig, axes = plt.subplots(1, len(residents), figsize=(max(5.2 * len(residents) + 1.5, 9), min(0.16 * n_days + 1.8, 11)),
                             sharey=True, squeeze=False)
    for ax, resident in zip(axes[0], residents):
        part = sessions[sessions["resident_id"] == resident]
        bars = []  # (day, left, width, color)
        for day, start, minutes, room in zip(
            (pd.to_datetime(part["date"]) - start_day).dt.days, part["start_hour"],
            part["duration_minutes"], part["dominant_room"],
        ):
            length = max(minutes / 60, 0.08)
            while length > 0:  # split sessions that cross midnight
                piece = min(length, 24 - start)
                bars.append((day, start, piece, color_of.get(room, NOISE)))
                length -= piece
                start, day = 0.0, day + 1
        if bars:
            days_, lefts, widths, colors = zip(*bars)
            ax.barh(days_, widths, left=lefts, height=0.82, color=colors, linewidth=0)
        _hour_axis(ax)
        ax.set_title(resident if len(residents) > 1 else title, fontsize=11)
    axes[0][0].set_ylim(n_days - 0.5, -0.5)
    axes[0][0].set_ylabel("Ngày quan sát")
    handles = [Patch(color=color_of[r], label=r) for r in top_rooms] + [Patch(color=NOISE, label="phòng khác")]
    fig.legend(handles=handles, loc="lower center", ncol=min(len(handles), 6), frameon=False, fontsize=9)
    if len(residents) > 1:
        fig.suptitle(title, x=0.01, ha="left", fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=170)
    plt.close(fig)


def plot_label_matrix(sessions: pd.DataFrame, profiles: pd.DataFrame, path: Path) -> None:
    """Share of each ground-truth activity inside every habit (evaluation only)."""
    if LABEL_COLUMN not in sessions.columns or profiles.empty:
        return
    habits = profiles[profiles["is_habit"]]
    if habits.empty:
        return
    part = sessions[sessions["cluster"].isin(habits["cluster"])]
    table = pd.crosstab(part["cluster"], part[LABEL_COLUMN], normalize="index")
    table = table.loc[:, table.max().sort_values(ascending=False).index]
    names = {row.cluster: f"C{row.cluster} · {row.room} · {row.typical_start}" for row in habits.itertuples()}
    if part["resident_id"].nunique() > 1:
        names = {row.cluster: f"C{row.cluster} · {row.resident_id} · {row.room} · {row.typical_start}"
                 for row in habits.itertuples()}

    fig, ax = plt.subplots(figsize=(1.0 * table.shape[1] + 4.5, 0.42 * table.shape[0] + 1.8))
    ax.imshow(table.to_numpy(), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for (i, j), v in np.ndenumerate(table.to_numpy()):
        if v >= 0.05:
            ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=8, color="white" if v > 0.6 else INK)
    ax.set_xticks(range(table.shape[1]))
    ax.set_xticklabels(table.columns, rotation=35, ha="right")
    ax.set_yticks(range(table.shape[0]))
    ax.set_yticklabels([names[c] for c in table.index])
    ax.spines[:].set_visible(False)
    ax.set_title("Đối chiếu thói quen tìm được với nhãn hoạt động thật (chỉ để đánh giá)")
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)
