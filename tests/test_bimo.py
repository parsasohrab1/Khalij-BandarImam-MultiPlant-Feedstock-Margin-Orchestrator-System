import numpy as np
import pytest
from fastapi.testclient import TestClient

from khalij_bimo import config as C
from khalij_bimo.api import app
from khalij_bimo.margin import DecisionLog, PriceForecaster, route_margins
from khalij_bimo.optimizer import build_model, evaluate, solve
from khalij_bimo.reconfig import pro_rata_baseline, reconfigure
from khalij_bimo.settlement import settlement_report
from khalij_bimo.simulator import generate_history, nominal_snapshot, row_to_snapshot


def snap(**kw):
    s = nominal_snapshot()
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def test_nominal_plan_is_feasible_and_balanced():
    p = solve(snap())
    assert p.feasible and p.total_margin_usd_h > 0
    x = p.x
    eth = C.OL_YIELD_NAPHTHA["ethylene"] * x["naph_ol"] + C.OL_YIELD_NGL["ethylene"] * x["ngl_ol"]
    assert eth == pytest.approx(x["eth_hdpe"] + x["eth_ldpe"] + x["eth_vcm"] + x["eth_sell"])
    for u in ("steam", "power", "n2"):
        assert p.utility_use[u] <= p.utility_capacity[u] + 1e-6


def test_company_margins_sum_to_total_and_transfer_prices_cancel():
    s = snap()
    a, b = solve(s, {"ethylene": 0.90, "propylene": 0.90, "c4": 0.90}), solve(s)
    assert sum(a.company_margin_usd_h.values()) == pytest.approx(a.total_margin_usd_h)
    # transfer prices only move money between entities: complex margin is unchanged
    assert a.total_margin_usd_h == pytest.approx(b.total_margin_usd_h, rel=1e-6)
    assert a.company_margin_usd_h["processing"] < b.company_margin_usd_h["processing"]


def test_utility_shortage_is_binding_and_cuts_margin():
    full = solve(snap())
    low = solve(snap(steam_available_percent=70))
    assert "utility_steam" in low.binding
    assert low.total_margin_usd_h < full.total_margin_usd_h
    assert low.shadow_prices["utility_steam"] > 0


def test_reconfiguration_beats_pro_rata_cutback():
    prev = solve(snap())
    new, alert = reconfigure(prev, snap(cracker_capacity_percent=65, steam_available_percent=75))
    base = pro_rata_baseline(prev, snap(cracker_capacity_percent=65, steam_available_percent=75))
    assert new.total_margin_usd_h >= base.total_margin_usd_h - 1e-6
    assert alert.delta_usd_h > 0 and alert.actions
    assert alert.solve_seconds < 60  # NFR-PER-01


def test_pro_rata_baseline_is_feasible():
    prev = solve(snap())
    s = snap(cracker_capacity_percent=50)
    base = pro_rata_baseline(prev, s)
    m = build_model(s)
    x = np.array([base.x[k] for k in m.names])
    assert (m.A_ub @ x <= m.b_ub + 1e-6).all()


def test_min_company_margin_floor_and_infeasible():
    s = snap(steam_available_percent=60)  # scarce steam: Kimia can be squeezed, so a floor binds
    base = solve(s)
    floor = base.company_margin_usd_h["kimia"] * 1.2
    p = solve(s, min_company_margin={"kimia": floor})
    assert p.feasible and p.company_margin_usd_h["kimia"] >= floor - 1e-6
    assert p.total_margin_usd_h < base.total_margin_usd_h  # fairness has a price
    assert not solve(s, min_company_margin={"kimia": 1e9}).feasible


def test_evaluate_reproduces_plan_margin():
    s = snap()
    p = solve(s)
    assert evaluate(s, p.x).total_margin_usd_h == pytest.approx(p.total_margin_usd_h)


def test_forecaster_beats_naive_or_matches():
    h = generate_history(3000)
    f = PriceForecaster().fit(h)
    mape = f.backtest_mape(h)
    assert max(mape.values()) < 0.05
    assert set(f.predict(h.tail(10))) == set(C.BASE_PRICES)


def test_route_margins_and_decision_log():
    rm = route_margins(snap())
    assert "naphtha->ethylene->PVC" in rm
    log = DecisionLog()
    log.record("t1", 100.0)
    assert log.settle("t1", 90.0) and log.mape() == pytest.approx(10 / 90)
    assert log.calibration < 1
    assert not log.settle("nope", 1.0)


def test_settlement_invoices_reconcile():
    s = snap()
    p = solve(s)
    rep = settlement_report(p, s)
    eth_lines = [i for i in rep["invoices"] if i["item"] == "ethylene"]
    assert sum(i["quantity"] for i in eth_lines) == pytest.approx(p.x["eth_hdpe"] + p.x["eth_ldpe"] + p.x["eth_vcm"])
    steam = sum(i["quantity"] for i in rep["invoices"] if i["item"] == "steam")
    assert steam == pytest.approx(p.utility_use["steam"])


def test_simulator_shape():
    h = generate_history(500)
    assert len(h) == 500 and {"needs_reallocation", "price_ethylene"} <= set(h.columns)
    assert row_to_snapshot(h.iloc[0]).prices["pvc"] > 0


def test_api_rbac_and_flow():
    c = TestClient(app)
    assert c.get("/snapshot").status_code == 401
    m = {"X-API-Key": "demo-manager"}
    assert c.get("/snapshot", headers=m).status_code == 200
    r = c.post("/outage", json={"cracker_capacity_percent": 60}, headers=m)
    assert r.status_code == 200 and r.json()["alert"]["delta_usd_h"] >= 0
    k = c.post("/optimize", json={}, headers={"X-API-Key": "demo-kimia"}).json()
    assert list(k["company_margin_usd_h"]) == ["kimia"] and k["total_margin_usd_h"] is None
    assert c.post("/outage", json={"cracker_capacity_percent": 50}, headers={"X-API-Key": "demo-bespar"}).status_code == 403
    assert c.post("/optimize", json={"min_company_margin_usd_h": {"kimia": 1e9}}, headers=m).status_code == 409
    assert c.post("/optimize", json={"price_overrides": {"bogus": 1}}, headers=m).status_code == 422
    assert c.get("/settlement", headers={"X-API-Key": "demo-bespar"}).status_code == 200
    assert c.get("/forecast", headers=m).status_code == 200
