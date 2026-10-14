"""Feedstock / intermediate-stream / utility optimizer (FR-ALLOC-01, FR-UTIL-01).

One linear model covers the four legal entities. Every decision variable carries a per-company
P&L coefficient (including internal transfer prices and utility tariffs), so the same model gives
(a) the complex-wide margin to maximise and (b) each subsidiary's margin for fairness floors.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog

from . import config as C
from .simulator import Snapshot

UTILS = ("steam", "power", "n2")


@dataclass
class Model:
    names: list[str]
    ub: np.ndarray
    econ: dict[str, np.ndarray]          # company -> $/h per unit of each variable
    util: dict[str, np.ndarray]          # utility -> use per unit of each variable
    A_ub: np.ndarray
    b_ub: np.ndarray
    ub_names: list[str]
    A_eq: np.ndarray
    b_eq: np.ndarray
    transfer_prices: dict[str, float]

    def total(self) -> np.ndarray:
        return sum(self.econ.values())


@dataclass
class Plan:
    status: str
    x: dict[str, float]
    total_margin_usd_h: float
    company_margin_usd_h: dict[str, float]
    utility_use: dict[str, float]
    utility_capacity: dict[str, float]
    binding: list[str]
    shadow_prices: dict[str, float]      # $/h gained per extra unit of the binding resource
    transfer_prices: dict[str, float] = field(default_factory=dict)

    @property
    def feasible(self) -> bool:
        return self.status in ("optimal", "evaluated")


def transfer_prices(prices: dict[str, float], fractions: dict[str, float] | None = None) -> dict[str, float]:
    fr = fractions or C.TRANSFER_PRICE_FRACTION
    return {k: prices[k] * f for k, f in fr.items()}


def effective_capacity(snap: Snapshot) -> dict:
    cap = dict(C.CAPACITY)
    cap["ol_feed"] *= snap.cracker_capacity_percent / 100
    cap["ar_feed"] *= snap.ar_capacity_percent / 100
    util = {
        "steam": C.UTILITY_CAPACITY["steam"] * snap.steam_available_percent / 100,
        "power": C.UTILITY_CAPACITY["power"] * snap.power_available_percent / 100,
        "n2": C.UTILITY_CAPACITY["n2"] * snap.n2_available_percent / 100,
    }
    return {"cap": cap, "util": util}


def build_model(snap: Snapshot, tp_fractions: dict[str, float] | None = None,
                min_company_margin: dict[str, float] | None = None) -> Model:
    p = snap.prices
    tp = transfer_prices(p, tp_fractions)
    eff = effective_capacity(snap)
    cap, ucap = eff["cap"], eff["util"]
    disc = 1 - C.EXPORT_DISCOUNT
    P, B, K, A = C.PROCESSING, C.BESPAR, C.KIMIA, C.ABNIROO

    V: dict[str, dict] = {}

    def var(name, ub=np.inf, unit=None, per=1.0):
        V[name] = dict(ub=ub, unit=unit, per=per, econ={c: 0.0 for c in C.COMPANIES})

    var("naph_ol", unit="ol"); var("ngl_ol", unit="ol"); var("naph_ar", unit="ar")
    var("eth_hdpe", unit="hdpe", per=C.HDPE_YIELD); var("eth_ldpe", unit="ldpe", per=C.LDPE_YIELD)
    var("eth_vcm", unit="pvc", per=C.PVC_PER_ETHYLENE); var("eth_sell", ub=C.EXPORT_CAP["ethylene"])
    var("prop_pp", unit="pp", per=C.PP_YIELD); var("prop_sell", ub=C.EXPORT_CAP["propylene"])
    var("c4_sr", unit="sr", per=C.SR_YIELD); var("c4_sell", ub=C.EXPORT_CAP["c4"])
    var("mtbe", ub=cap["mtbe"], unit="mtbe")

    def add(name, company, v):
        V[name]["econ"][company] += v

    # Processing: feed purchase, opex, by-product credit, BTX sales
    add("naph_ol", P, -p["naphtha"] - C.OPEX["ol"] + C.OL_YIELD_NAPHTHA["fuel"] * p["fuel"])
    add("ngl_ol", P, -p["ngl"] - C.OPEX["ol"] + C.OL_YIELD_NGL["fuel"] * p["fuel"])
    add("naph_ar", P, -p["naphtha"] - C.OPEX["ar"] + C.BTX_YIELD * p["btx"] * disc)
    # Intermediate-stream transfers: Processing sells at transfer price, buyer pays it
    for v, stream, buyer, final, yld, opex in [
        ("eth_hdpe", "ethylene", B, "hdpe", C.HDPE_YIELD, C.OPEX["hdpe"]),
        ("eth_ldpe", "ethylene", B, "ldpe", C.LDPE_YIELD, C.OPEX["ldpe"]),
        ("eth_vcm", "ethylene", K, "pvc", C.PVC_PER_ETHYLENE, C.OPEX["pvc"]),
        ("prop_pp", "propylene", B, "pp", C.PP_YIELD, C.OPEX["pp"]),
        ("c4_sr", "c4", B, "sr", C.SR_YIELD, C.OPEX["sr"]),
    ]:
        add(v, P, tp[stream])
        add(v, buyer, -tp[stream] + yld * p[final] - yld * opex)
    # MTBE: 0.45 t C4 from Processing at TP, methanol bought by Kimia on the market
    add("mtbe", P, C.MTBE_C4 * tp["c4"])
    add("mtbe", K, -C.MTBE_C4 * tp["c4"] - C.MTBE_METHANOL * p["methanol"] + p["mtbe"] - C.OPEX["mtbe"])
    # Spot/export sales by Processing
    add("eth_sell", P, p["ethylene"] * disc)
    add("prop_sell", P, p["propylene"] * disc)
    add("c4_sell", P, p["c4"] * disc)

    # Shared utilities: consumers pay tariff to Abniroo, Abniroo bears generation cost
    owner = {"ol": P, "ar": P, "hdpe": B, "ldpe": B, "pp": B, "sr": B, "pvc": K, "mtbe": K}
    util = {u: np.zeros(len(V)) for u in UTILS}
    for j, (name, d) in enumerate(V.items()):
        if d["unit"] is None:
            continue
        for u, spec in zip(UTILS, C.UTILITY_USE[d["unit"]]):
            use = spec * d["per"]
            util[u][j] = use
            add(name, owner[d["unit"]], -use * C.UTILITY_TARIFF[u])
            add(name, A, use * (C.UTILITY_TARIFF[u] - C.UTILITY_COST[u]))

    names = list(V)
    n = len(names)
    idx = {k: i for i, k in enumerate(names)}
    econ = {c: np.array([V[k]["econ"][c] for k in names]) for c in C.COMPANIES}
    ub = np.array([V[k]["ub"] for k in names], dtype=float)

    rows, rhs, rnames = [], [], []

    def le(name, coefs: dict, b):
        r = np.zeros(n)
        for k, v in coefs.items():
            r[idx[k]] = v
        rows.append(r); rhs.append(b); rnames.append(name)

    le("cracker_capacity", {"naph_ol": 1, "ngl_ol": 1}, cap["ol_feed"])
    le("aromatics_capacity", {"naph_ar": 1}, cap["ar_feed"])
    le("hdpe_capacity", {"eth_hdpe": C.HDPE_YIELD}, cap["hdpe"])
    le("ldpe_capacity", {"eth_ldpe": C.LDPE_YIELD}, cap["ldpe"])
    le("pvc_capacity", {"eth_vcm": C.PVC_PER_ETHYLENE}, cap["pvc"])
    le("pp_capacity", {"prop_pp": C.PP_YIELD}, cap["pp"])
    le("sr_capacity", {"c4_sr": C.SR_YIELD}, cap["sr"])
    le("naphtha_supply", {"naph_ol": 1, "naph_ar": 1}, C.SUPPLY["naphtha"])
    le("ngl_supply", {"ngl_ol": 1}, C.SUPPLY["ngl"])
    le("methanol_supply", {"mtbe": C.MTBE_METHANOL}, C.SUPPLY["methanol"])
    for u in UTILS:
        rows.append(util[u]); rhs.append(ucap[u]); rnames.append(f"utility_{u}")
    if min_company_margin:
        for c, floor in min_company_margin.items():
            rows.append(-econ[c]); rhs.append(-floor); rnames.append(f"floor_{c}")

    eq = np.zeros((3, n))
    eq[0, idx["naph_ol"]] = C.OL_YIELD_NAPHTHA["ethylene"]
    eq[0, idx["ngl_ol"]] = C.OL_YIELD_NGL["ethylene"]
    for k in ("eth_hdpe", "eth_ldpe", "eth_vcm", "eth_sell"):
        eq[0, idx[k]] = -1
    eq[1, idx["naph_ol"]] = C.OL_YIELD_NAPHTHA["propylene"]
    eq[1, idx["ngl_ol"]] = C.OL_YIELD_NGL["propylene"]
    eq[1, idx["prop_pp"]] = -1
    eq[1, idx["prop_sell"]] = -1
    eq[2, idx["naph_ol"]] = C.OL_YIELD_NAPHTHA["c4"]
    eq[2, idx["ngl_ol"]] = C.OL_YIELD_NGL["c4"]
    eq[2, idx["c4_sr"]] = -1
    eq[2, idx["mtbe"]] = -C.MTBE_C4
    eq[2, idx["c4_sell"]] = -1

    return Model(names, ub, econ, util, np.array(rows), np.array(rhs), rnames, eq, np.zeros(3), tp)


def _plan_from_x(m: Model, x: np.ndarray, status: str, res=None) -> Plan:
    cm = {c: float(m.econ[c] @ x) for c in C.COMPANIES}
    uu = {u: float(m.util[u] @ x) for u in UTILS}
    ucap = {u: float(m.b_ub[m.ub_names.index(f"utility_{u}")]) for u in UTILS}
    binding, shadow = [], {}
    if res is not None and hasattr(res, "ineqlin"):
        for name, slack, mu in zip(m.ub_names, res.ineqlin.residual, res.ineqlin.marginals):
            if slack < 1e-6 and abs(mu) > 1e-6:
                binding.append(name)
                shadow[name] = float(-mu)  # linprog minimises -margin => gain per extra unit of resource
    return Plan(status, {k: float(v) for k, v in zip(m.names, x)}, float(sum(cm.values())), cm, uu, ucap,
                binding, shadow, m.transfer_prices)


def solve(snap: Snapshot, tp_fractions: dict[str, float] | None = None,
          min_company_margin: dict[str, float] | None = None) -> Plan:
    m = build_model(snap, tp_fractions, min_company_margin)
    res = linprog(-m.total(), A_ub=m.A_ub, b_ub=m.b_ub, A_eq=m.A_eq, b_eq=m.b_eq,
                  bounds=list(zip(np.zeros(len(m.names)), m.ub)), method="highs")
    if res.status != 0:
        zero = {c: 0.0 for c in C.COMPANIES}
        return Plan("infeasible" if res.status == 2 else "failed", {k: 0.0 for k in m.names}, 0.0, zero,
                    {u: 0.0 for u in UTILS}, {u: 0.0 for u in UTILS}, [], {}, m.transfer_prices)
    return _plan_from_x(m, res.x, "optimal", res)


def evaluate(snap: Snapshot, x: dict[str, float], tp_fractions=None) -> Plan:
    """Margin of a fixed flow vector under a snapshot's prices (realized-margin accounting)."""
    m = build_model(snap, tp_fractions)
    return _plan_from_x(m, np.array([x[k] for k in m.names]), "evaluated")
