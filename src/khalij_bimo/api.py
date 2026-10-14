"""REST API / command-center backend (R-GEN-03, NFR-SEC-01).

Run:  uvicorn khalij_bimo.api:app --reload
Auth: header `X-API-Key`; keys map to roles via env KHALIJ_KEYS="key1:manager,key2:bespar,..."
(demo defaults below). Subsidiary roles see only their own margin/invoices; `manager` sees all.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import config as C
from .margin import DecisionLog, PriceForecaster, route_margins
from .optimizer import Plan, solve
from .reconfig import reconfigure
from .settlement import settlement_report
from .simulator import Snapshot, generate_history, nominal_snapshot, row_to_snapshot

ROLES = set(C.COMPANIES) | {"manager"}


def _keys() -> dict[str, str]:
    raw = os.environ.get("KHALIJ_KEYS", "demo-manager:manager,demo-processing:processing,"
                                         "demo-bespar:bespar,demo-kimia:kimia,demo-abniroo:abniroo")
    out = {}
    for pair in raw.split(","):
        k, _, r = pair.partition(":")
        if r.strip() in ROLES:
            out[k.strip()] = r.strip()
    return out


def role(x_api_key: str = Header(default="")) -> str:
    r = _keys().get(x_api_key)
    if r is None:
        raise HTTPException(401, "invalid API key")
    return r


class Overrides(BaseModel):
    cracker_capacity_percent: float | None = Field(None, ge=0, le=100)
    steam_available_percent: float | None = Field(None, ge=0, le=100)
    power_available_percent: float | None = Field(None, ge=0, le=100)
    n2_available_percent: float | None = Field(None, ge=0, le=100)
    ar_capacity_percent: float | None = Field(None, ge=0, le=100)
    price_overrides: dict[str, float] = {}
    min_company_margin_usd_h: dict[str, float] = {}


class Realized(BaseModel):
    timestamp: str
    realized_margin_usd_h: float


class State:
    def __init__(self):
        self.history = generate_history(3000)
        self.forecaster = PriceForecaster().fit(self.history)
        self.snapshot: Snapshot = row_to_snapshot(self.history.iloc[-1])
        self.plan: Plan = solve(self.snapshot)
        self.log = DecisionLog()
        self.log.record(self.snapshot.timestamp.isoformat(), self.plan.total_margin_usd_h, self.plan.x)


state = State()
app = FastAPI(title="Khalij-BIMO", version="0.1.0")


def _apply(snap: Snapshot, o: Overrides) -> Snapshot:
    from dataclasses import replace
    fields = {k: v for k, v in o.model_dump(exclude={"price_overrides", "min_company_margin_usd_h"}).items()
              if v is not None}
    bad = set(o.price_overrides) - set(snap.prices)
    if bad:
        raise HTTPException(422, f"unknown price keys: {sorted(bad)}")
    return replace(snap, prices={**snap.prices, **o.price_overrides}, **fields)


def _view(plan: Plan, r: str) -> dict:
    d = asdict(plan)
    if r != "manager":
        d["company_margin_usd_h"] = {r: d["company_margin_usd_h"][r]}
        d["total_margin_usd_h"] = None
    return d


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/snapshot")
def get_snapshot(r: str = Depends(role)):
    s = state.snapshot
    return {"timestamp": s.timestamp.isoformat(), "prices": s.prices,
            "cracker_capacity_percent": s.cracker_capacity_percent,
            "steam_available_percent": s.steam_available_percent,
            "power_available_percent": s.power_available_percent,
            "route_margins_usd_t": route_margins(s)}


@app.post("/optimize")
def optimize(o: Overrides = Overrides(), r: str = Depends(role)):
    snap = _apply(state.snapshot, o)
    plan = solve(snap, min_company_margin=o.min_company_margin_usd_h or None)
    if not plan.feasible:
        raise HTTPException(409, f"no feasible allocation ({plan.status}); relax company margin floors")
    if r == "manager":
        state.snapshot, state.plan = snap, plan
        state.log.record(snap.timestamp.isoformat(), plan.total_margin_usd_h, plan.x)
    return _view(plan, r)


@app.post("/outage")
def outage(o: Overrides, r: str = Depends(role)):
    """Apply an outage/fluctuation, reconfigure flows, return the alert with the value of acting."""
    if r != "manager":
        raise HTTPException(403, "only the complex manager can trigger a complex-wide reconfiguration")
    snap = _apply(state.snapshot, o)
    new, alert = reconfigure(state.plan, snap, min_company_margin=o.min_company_margin_usd_h or None)
    if not new.feasible:
        raise HTTPException(409, f"no feasible allocation ({new.status})")
    state.snapshot, state.plan = snap, new
    state.log.record(snap.timestamp.isoformat(), new.total_margin_usd_h, new.x)
    return {"alert": asdict(alert), "plan": _view(new, r)}


@app.get("/settlement")
def settlement(r: str = Depends(role)):
    rep = settlement_report(state.plan, state.snapshot)
    if r != "manager":
        rep["invoices"] = [i for i in rep["invoices"] if r in (i["seller"], i["buyer"])]
        rep["company_margin_usd_h"] = {r: rep["company_margin_usd_h"][r]}
        rep["complex_margin_usd_h"] = None
    return rep


@app.post("/realized")
def realized(b: Realized, r: str = Depends(role)):
    if r != "manager":
        raise HTTPException(403, "manager only")
    if not state.log.settle(b.timestamp, b.realized_margin_usd_h):
        raise HTTPException(404, "no decision recorded for that timestamp")
    return {"calibration": state.log.calibration, "mape": state.log.mape()}


@app.get("/forecast")
def forecast(r: str = Depends(role)):
    return {"next_prices": state.forecaster.predict(state.history.tail(10)),
            "backtest_mape": state.forecaster.backtest_mape(state.history)}
