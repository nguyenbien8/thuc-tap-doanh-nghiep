"""Load the STRANDS *Long-term person activity* dataset into the project schema.

Dataset page : https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity.html
Archive      : https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity/activity.zip
Cite         : Coppola, Krajník, Bellotto, Duckett – "Learning temporal context
               for activity recognition", ECAI 2016; and for the Aruba subset
               D. J. Cook – "Learning setting-generalized activity models for
               smart spaces", IEEE Intelligent Systems, 2010 (CASAS).

Format of one dataset folder (``aruba/`` or ``witham/``)
---------------------------------------------------------
``location.min`` / ``activity.min``
    One integer per line, one line per minute since midnight of day 1.
``location.names`` / ``activity.names``
    One name per line; the integer codes index into these lists.

Code bases (checked on the data, see ``reports/02_du_lieu.md``)
---------------------------------------------------------------------
* activity codes are 0-based (code 0 = "None"/"Outside");
* location codes are **1-based**: in Aruba code 1 co-occurs with *Sleeping*
  (Master Bedroom), 2 with *Bed_to_Toilet* (Master Bathroom), 3 with *Relax*
  (Living Room), 4 with *Meal_Preparation* (Kitchen). Unmapped codes are kept
  as ``location_<code>`` so nothing is silently renamed.

Conversion
----------
Every minute becomes one ``presence`` event of the person in a room – exactly
what a room-level localisation sensor would emit. The activity name is copied
to ``activity_label`` for evaluation only.
"""
from __future__ import annotations

import io
from pathlib import Path
import urllib.request
import zipfile
import numpy as np
import pandas as pd

ARCHIVE_URL = "https://lcas.lincoln.ac.uk/nextcloud/shared/datasets/activity/activity.zip"


def download_strands(target_dir: str | Path = "data/raw/strands", url: str = ARCHIVE_URL) -> Path:
    """Download and unzip the public archive (≈30 kB); returns the target folder."""
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read()
    zipfile.ZipFile(io.BytesIO(payload)).extractall(target)
    return target


def _read_codes(path: Path) -> np.ndarray:
    return pd.read_csv(path, header=None, sep=r"\s+").iloc[:, 0].to_numpy(dtype=int)


def _read_names(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _slug(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def load_strands(
    folder: str | Path,
    resident_id: str | None = None,
    start_date: str = "2010-11-04",
    location_base: int = 1,
    activity_base: int = 0,
    location_overrides: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Convert one STRANDS folder into the 7-column event schema (+ label).

    Parameters
    ----------
    folder:
        Path to ``aruba`` or ``witham`` inside the extracted archive.
    resident_id:
        Identifier to use (default: the folder name).
    start_date:
        Nominal calendar date of minute 0. The files contain no dates, so
        weekday information derived from it is not meaningful.
    location_base, activity_base:
        Index of the first name in the ``.names`` files.
    location_overrides:
        Optional ``{code: room_name}`` corrections, documented in the report.
    """
    folder = Path(folder)
    locations = _read_codes(folder / "location.min")
    activities = _read_codes(folder / "activity.min")
    if len(locations) != len(activities):
        raise ValueError("location.min and activity.min have different lengths")

    location_names = _read_names(folder / "location.names")
    activity_names = _read_names(folder / "activity.names")
    overrides = {int(k): v for k, v in (location_overrides or {}).items()}

    def room_of(code: int) -> str:
        if code in overrides:
            return _slug(overrides[code])
        i = code - location_base
        return _slug(location_names[i]) if 0 <= i < len(location_names) else f"location_{code}"

    def activity_of(code: int) -> str:
        i = code - activity_base
        return activity_names[i] if 0 <= i < len(activity_names) else f"unknown_{code}"

    rooms = pd.Series(locations).map({c: room_of(c) for c in np.unique(locations)})
    labels = pd.Series(activities).map({c: activity_of(c) for c in np.unique(activities)})
    return pd.DataFrame({
        "timestamp": pd.Timestamp(start_date) + pd.to_timedelta(np.arange(len(locations)), unit="min"),
        "resident_id": resident_id or folder.name,
        "room": rooms,
        "sensor_type": "presence",
        "sensor_id": "loc_" + pd.Series(locations).astype(str),
        "value": 1.0,
        "event_type": "presence",
        "activity_label": labels,
    })
