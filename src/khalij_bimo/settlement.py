"""Inter-company settlement (R-GEN-04, phase 5): invoices at the internal transfer price and per-entity P&L.

Interface to the ERP/settlement system is a plain list of invoice lines (`as_records()`); a real
connector would post these. Utility invoices are Abniroo -> consumers at tariff.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from . import config as C
from .optimizer import Plan, transfer_prices


@dataclass
class Invoice:
    seller: str
    buyer: str
    item: str
    quantity: float
    unit: str
    unit_price: float

    @property
    def amount_usd_h(self) -> float:
        return self.quantity * self.unit_price


def intercompany_invoices(plan: Plan, prices: dict[str, float], tp_fractions=None) -> list[Invoice]:
    tp = transfer_prices(prices, tp_fractions)
    x = plan.x
    P, B, K = C.PROCESSING, C.BESPAR, C.KIMIA
    lines = [
        (P, B, "ethylene", x["eth_hdpe"] + x["eth_ldpe"], tp["ethylene"]),
        (P, K, "ethylene", x["eth_vcm"], tp["ethylene"]),
        (P, B, "propylene", x["prop_pp"], tp["propylene"]),
        (P, B, "c4", x["c4_sr"], tp["c4"]),
        (P, K, "c4", C.MTBE_C4 * x["mtbe"], tp["c4"]),
    ]
    inv = [Invoice(s, b, i, q, "t/h", pr) for s, b, i, q, pr in lines if q > 1e-9]
    return inv


def utility_invoices(plan: Plan, m_util_by_company: dict[str, dict[str, float]]) -> list[Invoice]:
    unit = {"steam": "t/h", "power": "MW", "n2": "Nm3/h"}
    out = []
    for company, use in m_util_by_company.items():
        for u, q in use.items():
            if q > 1e-9:
                out.append(Invoice(C.ABNIROO, company, u, q, unit[u], C.UTILITY_TARIFF[u]))
    return out


def utility_draw_by_company(plan: Plan, snap) -> dict[str, dict[str, float]]:
    """Utility draw per consuming company, from the model's utility rows."""
    import numpy as np
    from .optimizer import UTILS, build_model
    m = build_model(snap)
    x = np.array([plan.x[k] for k in m.names])
    owner = {"naph_ol": C.PROCESSING, "ngl_ol": C.PROCESSING, "naph_ar": C.PROCESSING,
             "eth_hdpe": C.BESPAR, "eth_ldpe": C.BESPAR, "prop_pp": C.BESPAR, "c4_sr": C.BESPAR,
             "eth_vcm": C.KIMIA, "mtbe": C.KIMIA}
    res = {c: {u: 0.0 for u in UTILS} for c in (C.PROCESSING, C.BESPAR, C.KIMIA)}
    for j, name in enumerate(m.names):
        if name in owner:
            for u in UTILS:
                res[owner[name]][u] += float(m.util[u][j] * x[j])
    return res


def settlement_report(plan: Plan, snap, tp_fractions=None) -> dict:
    inv = intercompany_invoices(plan, snap.prices, tp_fractions) + utility_invoices(
        plan, utility_draw_by_company(plan, snap))
    return {
        "transfer_prices_usd_t": plan.transfer_prices,
        "company_margin_usd_h": plan.company_margin_usd_h,
        "complex_margin_usd_h": plan.total_margin_usd_h,
        "invoices": [{**asdict(i), "amount_usd_h": round(i.amount_usd_h, 2)} for i in inv],
    }
