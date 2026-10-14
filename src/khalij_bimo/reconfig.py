"""Automatic reconfiguration after an outage / fluctuation (FR-ALLOC-02, FR-ALERT-01).

Baseline = what happens today: the previous plan is cut back pro-rata until it fits the new limits
(no re-routing). Alternative = full re-optimisation. The difference is the value of the alert.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, replace

import numpy as np

from . import config as C
from .optimizer import Model, Plan, _plan_from_x, build_model, solve
from .simulator import Snapshot


def pro_rata_baseline(prev: Plan, new_snap: Snapshot, tp_fractions=None) -> Plan:
    """Scale the previous flows uniformly so every capacity/utility/supply limit holds (balances are homogeneous)."""
    m: Model = build_model(new_snap, tp_fractions)
    x = np.array([prev.x[k] for k in m.names])
    use = m.A_ub @ x
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = np.where(use > 1e-9, m.b_ub / use, np.inf)
    ub_ratio = np.where(x > 1e-9, m.ub / np.where(x > 1e-9, x, 1), np.inf)
    s = float(min(1.0, ratios.min(), ub_ratio.min()))
    return _plan_from_x(m, x * s, "evaluated")


@dataclass
class Alert:
    severity: str
    message: str
    delta_usd_h: float
    baseline_margin_usd_h: float
    optimized_margin_usd_h: float
    actions: list[dict] = field(default_factory=list)
    solve_seconds: float = 0.0


def _severity(delta: float, base: float) -> str:
    rel = delta / base if base else 0
    return "critical" if rel > 0.10 else "warning" if rel > 0.02 else "info"


def reconfigure(prev: Plan, new_snap: Snapshot, tp_fractions=None, min_company_margin=None,
                top_actions: int = 6) -> tuple[Plan, Alert]:
    t0 = time.perf_counter()
    new = solve(new_snap, tp_fractions, min_company_margin)
    dt = time.perf_counter() - t0
    base = pro_rata_baseline(prev, new_snap, tp_fractions)
    delta = new.total_margin_usd_h - base.total_margin_usd_h
    diffs = sorted(
        ({"variable": k, "from_t_h": round(base.x[k], 2), "to_t_h": round(new.x[k], 2),
          "change_t_h": round(new.x[k] - base.x[k], 2)} for k in new.x),
        key=lambda a: -abs(a["change_t_h"]))
    actions = [a for a in diffs if abs(a["change_t_h"]) >= 0.05][:top_actions]
    cause = []
    if new_snap.cracker_capacity_percent < 100:
        cause.append(f"cracker at {new_snap.cracker_capacity_percent:.0f}%")
    if new_snap.steam_available_percent < 100:
        cause.append(f"steam at {new_snap.steam_available_percent:.0f}%")
    if new_snap.power_available_percent < 100:
        cause.append(f"power at {new_snap.power_available_percent:.0f}%")
    msg = (f"Reallocation recommended ({', '.join(cause) or 'market change'}): "
           f"+{delta:,.0f} USD/h versus pro-rata cutback; binding: {', '.join(new.binding) or 'none'}.")
    return new, Alert(_severity(delta, base.total_margin_usd_h), msg, delta, base.total_margin_usd_h,
                      new.total_margin_usd_h, actions, dt)
