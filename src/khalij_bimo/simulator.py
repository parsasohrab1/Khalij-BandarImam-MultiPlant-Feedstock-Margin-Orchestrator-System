"""Multi-entity data simulator (stands in for the 4 DCS feeds + commodity-exchange price feed)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .config import BASE_PRICES

# Price-series amplitude (fraction of base) and phase, per product
_VOL = {"ethylene": 0.063, "hdpe": 0.07, "pvc": 0.055, "propylene": 0.06, "c4": 0.06,
        "btx": 0.05, "ldpe": 0.07, "pp": 0.06, "sr": 0.05, "mtbe": 0.06,
        "naphtha": 0.05, "ngl": 0.05, "methanol": 0.05, "fuel": 0.04}


@dataclass
class Snapshot:
    """One instant of the complex: market prices + unit/utility availability (all in %)."""
    timestamp: datetime
    prices: dict[str, float]
    cracker_capacity_percent: float = 100.0
    steam_available_percent: float = 100.0
    power_available_percent: float = 100.0
    n2_available_percent: float = 100.0
    ar_capacity_percent: float = 100.0
    extras: dict = field(default_factory=dict)


def generate_history(n: int = 10_000, seed: int = 7, start: datetime | None = None,
                     step_minutes: float = 1.0) -> pd.DataFrame:
    """Time series with the variables from the SRS plus the full price deck."""
    rng = np.random.default_rng(seed)
    start = start or datetime(2026, 9, 14, 8, 0, 0)
    ts = [start + timedelta(minutes=step_minutes * i) for i in range(n)]
    t = np.linspace(0, 20 * np.pi, n)
    d = {"timestamp": ts}
    # AR(1) noise gives realistic persistence for the forecaster
    for k, (name, base) in enumerate(BASE_PRICES.items()):
        noise = np.zeros(n)
        e = rng.normal(0, base * 0.003, n)
        for i in range(1, n):
            noise[i] = 0.9 * noise[i - 1] + e[i]
        d[f"price_{name}"] = base * (1 + _VOL[name] * np.sin(t * (0.02 + 0.004 * k) + k)) + noise
    d["cracker_capacity_percent"] = np.clip(92 + 5 * np.sin(t * 0.08) + rng.normal(0, 2, n), 60, 100)
    d["steam_available_percent"] = np.clip(88 + 6 * np.sin(t * 0.05) + rng.normal(0, 3, n), 50, 100)
    d["power_available_percent"] = np.clip(90 + 4 * np.sin(t * 0.06 + 0.5) + rng.normal(0, 2, n), 50, 100)
    d["n2_available_percent"] = np.clip(95 + rng.normal(0, 2, n), 70, 100)
    df = pd.DataFrame(d)
    df["needs_reallocation"] = ((df.cracker_capacity_percent < 75) | (df.steam_available_percent < 75)).astype(int)
    return df


def row_to_snapshot(row: pd.Series) -> Snapshot:
    return Snapshot(
        timestamp=pd.Timestamp(row["timestamp"]).to_pydatetime(),
        prices={k: float(row[f"price_{k}"]) for k in BASE_PRICES},
        cracker_capacity_percent=float(row["cracker_capacity_percent"]),
        steam_available_percent=float(row["steam_available_percent"]),
        power_available_percent=float(row["power_available_percent"]),
        n2_available_percent=float(row["n2_available_percent"]),
    )


def nominal_snapshot() -> Snapshot:
    return Snapshot(timestamp=datetime(2026, 9, 14, 8, 0, 0), prices=dict(BASE_PRICES))
