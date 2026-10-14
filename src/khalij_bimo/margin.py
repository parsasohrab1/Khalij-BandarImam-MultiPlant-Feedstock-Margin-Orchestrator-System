"""Margin prediction (FR-MARGIN-01) and realized-margin feedback loop (FR-LOOP-01).

* PriceForecaster: ridge regression on lagged prices -> next-step price deck (ML component).
* route_margins(): instantaneous gross margin per feedstock->product route, USD per t of feed.
* DecisionLog: stores predicted vs. realized margin; derives a calibration factor and MAPE
  (NFR-PER-02 target: < 10 % error vs. settlement).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from . import config as C
from .simulator import BASE_PRICES, Snapshot


class PriceForecaster:
    def __init__(self, lags: int = 5, horizon: int = 1, alpha: float = 1.0):
        self.lags, self.horizon, self.alpha = lags, horizon, alpha
        self.models: dict[str, Ridge] = {}
        self.fitted = False

    def _xy(self, s: np.ndarray):
        n = len(s) - self.lags - self.horizon + 1
        X = np.stack([s[i:i + self.lags] for i in range(n)])
        y = s[self.lags + self.horizon - 1: self.lags + self.horizon - 1 + n]
        # model the change relative to the last observed price
        return X - X[:, -1:], y - X[:, -1], X[:, -1]

    def fit(self, history: pd.DataFrame) -> "PriceForecaster":
        for k in BASE_PRICES:
            X, y, _ = self._xy(history[f"price_{k}"].to_numpy())
            self.models[k] = Ridge(alpha=self.alpha).fit(X, y)
        self.fitted = True
        return self

    def predict(self, recent: pd.DataFrame) -> dict[str, float]:
        """`recent`: last >= `lags` rows of the history frame."""
        out = {}
        for k in BASE_PRICES:
            w = recent[f"price_{k}"].to_numpy()[-self.lags:]
            out[k] = float(w[-1] + self.models[k].predict((w - w[-1]).reshape(1, -1))[0])
        return out

    def backtest_mape(self, history: pd.DataFrame, test_frac: float = 0.2) -> dict[str, float]:
        cut = int(len(history) * (1 - test_frac))
        res = {}
        for k in BASE_PRICES:
            X, y, last = self._xy(history[f"price_{k}"].to_numpy()[cut - self.lags:])
            pred = last + self.models[k].predict(X)
            actual = last + y
            res[k] = float(np.mean(np.abs(pred - actual) / actual))
        return res


def route_margins(snap: Snapshot) -> dict[str, float]:
    """USD per t of feed for the main feedstock -> final-product routes (before utilities' tariff)."""
    p = snap.prices
    disc = 1 - C.EXPORT_DISCOUNT
    ol_n, ol_g = C.OL_YIELD_NAPHTHA, C.OL_YIELD_NGL
    def ol_value(y, eth, prop, c4):
        return y["ethylene"] * eth + y["propylene"] * prop + y["c4"] * c4 + y["fuel"] * p["fuel"] - C.OPEX["ol"]
    eth_hdpe = C.HDPE_YIELD * p["hdpe"] - C.HDPE_YIELD * C.OPEX["hdpe"]
    eth_ldpe = C.LDPE_YIELD * p["ldpe"] - C.LDPE_YIELD * C.OPEX["ldpe"]
    eth_pvc = C.PVC_PER_ETHYLENE * (p["pvc"] - C.OPEX["pvc"])
    prop_pp = C.PP_YIELD * (p["pp"] - C.OPEX["pp"])
    c4_sr = C.SR_YIELD * (p["sr"] - C.OPEX["sr"])
    best_eth = max(eth_hdpe, eth_ldpe, eth_pvc, p["ethylene"] * disc)
    best_prop = max(prop_pp, p["propylene"] * disc)
    best_c4 = max(c4_sr / 1.0, p["c4"] * disc)  # per t C4
    return {
        "naphtha->ethylene->HDPE": ol_n["ethylene"] * eth_hdpe - p["naphtha"],
        "naphtha->ethylene->LDPE": ol_n["ethylene"] * eth_ldpe - p["naphtha"],
        "naphtha->ethylene->PVC": ol_n["ethylene"] * eth_pvc - p["naphtha"],
        "naphtha->OL (best use of all streams)": ol_value(ol_n, best_eth, best_prop, best_c4) - p["naphtha"],
        "NGL->OL (best use of all streams)": ol_value(ol_g, best_eth, best_prop, best_c4) - p["ngl"],
        "naphtha->aromatics (BTX)": C.BTX_YIELD * p["btx"] * disc - C.OPEX["ar"] - p["naphtha"],
    }


@dataclass
class DecisionRecord:
    ts: str
    predicted_usd_h: float
    realized_usd_h: float | None = None
    plan: dict = field(default_factory=dict)


class DecisionLog:
    def __init__(self, maxlen: int = 5000, ewma: float = 0.2):
        self.records: deque[DecisionRecord] = deque(maxlen=maxlen)
        self.ewma = ewma
        self.calibration = 1.0   # realized / predicted

    def record(self, ts: str, predicted: float, plan: dict | None = None) -> DecisionRecord:
        r = DecisionRecord(ts, predicted, None, plan or {})
        self.records.append(r)
        return r

    def settle(self, ts: str, realized: float) -> bool:
        for r in reversed(self.records):
            if r.ts == ts:
                r.realized_usd_h = realized
                if r.predicted_usd_h:
                    ratio = realized / r.predicted_usd_h
                    self.calibration = (1 - self.ewma) * self.calibration + self.ewma * ratio
                return True
        return False

    def mape(self) -> float | None:
        done = [r for r in self.records if r.realized_usd_h not in (None, 0)]
        if not done:
            return None
        return float(np.mean([abs(r.predicted_usd_h - r.realized_usd_h) / abs(r.realized_usd_h) for r in done]))

    def calibrated(self, predicted: float) -> float:
        return predicted * self.calibration
