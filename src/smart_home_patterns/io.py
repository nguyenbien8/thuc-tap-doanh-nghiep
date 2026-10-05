from __future__ import annotations

from pathlib import Path
import pandas as pd
import yaml

DEFAULT_CONFIG = Path("configs/config.yaml")


def load_config(path: str | Path | None = None) -> dict:
    """Load a YAML configuration file (default: ``configs/config.yaml``).

    Relative paths inside the config are resolved against the current working
    directory, so commands are meant to be run from the project root.
    """
    target = Path(path) if path is not None else DEFAULT_CONFIG
    if not target.exists():
        raise FileNotFoundError(
            f"Config file not found: {target.resolve()}\n"
            "Run commands from the project root directory, or pass --config <path>."
        )
    with target.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_events(path: str | Path) -> pd.DataFrame:
    """Read a CSV event log into a DataFrame."""
    return pd.read_csv(path)


def write_frame(frame: pd.DataFrame, path: str | Path) -> None:
    """Write a DataFrame to CSV, creating parent directories if needed."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
