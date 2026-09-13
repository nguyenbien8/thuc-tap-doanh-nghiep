from __future__ import annotations

from pathlib import Path
import pandas as pd
import yaml


def load_config(path: str | Path = "configs/config.yaml") -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_events(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_frame(frame: pd.DataFrame, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
