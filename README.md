# Khalij-BandarImam-MultiPlant-Feedstock-Margin-Orchestrator-System (Khalij-BIMO)

## Intelligent system for real-time feedstock allocation, intermediate-stream reconfiguration, and simultaneous gross-margin optimization across the 4 subsidiary companies of the Bandar Imam Petrochemical Complex — a dedicated BIPC product

> This document is a **dedicated** product for Bandar Imam Petrochemical Company (BIPC). Note: the holding's general product 1 (process parameter optimization of a single reactor) had previously been assigned to this company, but that product sees only the "single reactor" level. The present product covers BIPC's real and unique gap — coordination **among four independent subsidiaries** with shared feedstock and utilities — and complements (does not compete with) product 1.

---

## 0. Understanding Bandar Imam Petrochemical Company (based on a study of the official site/PGPIC) and the technical gap

**Sources:** [PGPIC — Bandar Imam company page](https://pgpic.ir/%D8%B4%D8%B1%DA%A9%D8%AA-%D9%87%D8%A7%DB%8C-%D8%AA%D8%A7%D8%A8%D8%B9%D9%87/%D9%85%D8%AC%D8%AA%D9%85%D8%B9-%D9%87%D8%A7%DB%8C-%D8%AA%D9%88%D9%84%DB%8C%D8%AF%DB%8C/%D8%B4%D8%B1%DA%A9%D8%AA-%D9%BE%D8%AA%D8%B1%D9%88%D8%B4%DB%8C%D9%85%DB%8C-%D8%A8%D9%86%D8%AF%D8%B1-%D8%A7%D9%85%D8%A7%D9%85), [BIPC Products](https://bipc.ir/en/products/), [Persian Wikipedia](https://fa.wikipedia.org/wiki/%D8%B4%D8%B1%DA%A9%D8%AA_%D9%BE%D8%AA%D8%B1%D9%88%D8%B4%DB%8C%D9%85%DB%8C_%D8%A8%D9%86%D8%AF%D8%B1_%D8%A7%D9%85%D8%A7%D9%85)

### BIPC's unique structure (a key point for product design)

Bandar Imam is **Iran's largest petrochemical complex** (nominal capacity 4,748 kilotons/year, 270 hectares) and, unlike most of the holding's companies, consists of **four separate subsidiaries** with interdependent products and utilities:

| Subsidiary | Units | Products |
|---|---|---|
| Bandar Imam Processing | NF (naphtha), OL (olefin/Lummus steam cracker), AR (aromatics), PX (paraxylene) | Ethylene (411 kilotons), propylene, butane, benzene/toluene/xylene |
| Bandar Imam Polymer (Bespar) | HDPE, LDPE, PP, BD/SR | Light/heavy polyethylene, polypropylene, butadiene/synthetic rubber |
| Bandar Imam Kimia | CA (chlor-alkali), DC (EDC), VCM, PVC, MTBE | Caustic, PVC, MTBE |
| Bandar Imam Abniroo | Electricity, steam, water, air, nitrogen | Shared utilities of the entire complex |

### Technical Gap Relative to the Holding's Products 1 to 4

| Holding product | Why it is not enough for BIPC |
|---|---|
| Product 1 (process parameter optimization) | Its level is **one reactor/one unit** (e.g., only the OL cracker); it does not enter the decision "which feedstock goes to which subsidiary with what priority" or the utility interdependence among the 4 companies |
| Product 3 (energy/carbon) | Designed for the single-product PTA unit and assigned to Shahid Tondgooyan; it does not cover the case of "shared utilities among 4 legally independent companies" |
| Product 4 (asset monitoring) | Assigned to Karoun company and sees the equipment/furnace level, not the feedstock/margin allocation level among companies |

**Conclusion:** BIPC needs a "complex-level orchestration" layer that goes beyond one unit or one subsidiary and **simultaneously sees the four companies with feedstock, shared-utility and market constraints** — exactly what is not covered by any of products 1 to 4.

---

## 1. Patent Background and Competitive Analysis

| No. | Existing patent/technology | Main limitation | Difference of this product |
|---|---|---|---|
| 1 | **US 11,663,546 B2** – *Automated evaluation of refinery and petrochemical feedstocks using historical market prices, ML and algebraic planning* | Evaluation of feedstock profitability for **a single complex**; does not consider allocation among multiple subsidiaries with separate legal/accounting structures | Feedstock allocation with margin optimization at the level of **4 subsidiaries simultaneously** with an internal transfer price |
| 2 | **US 11,886,157 B2** – *Operational optimization of industrial steam and power utility systems* | Steam/power system optimization independent of feedstock/product allocation decisions | Direct linking of the Abniroo utility capacity to the feedstock allocation decision of Processing/Bespar/Kimia in one model |
| 3 | Mu Sigma AI-Driven S&OP — ranking units by margin and automatic redistribution of olefins during cracker outage | General commercial/consulting architecture, without a specific patent and without modeling shared-utility constraints of the Iranian petrochemical industry | Industrial implementation with real DCS input + utility constraint + connection to the inter-company settlement financial system |
| 4 | Integrated refinery-petrochemical modeling for company-level optimization (ScienceDirect) | Research/academic, long-term planning level (monthly/quarterly), not real-time operational | **Hourly real-time** optimization with real feedback from outages/production fluctuations |

### Core Patentable Claim

> **"A Multi-Legal-Entity Real-Time Orchestration system that, for the first time, solves feedstock allocation (naphtha/NGL/methanol), reconfiguration of intermediate streams (ethylene/propylene/butadiene) among independent subsidiaries of a petrochemical complex, and allocation of limited shared utility capacity (steam/power/nitrogen) in a single optimization model aimed at maximizing the total gross margin of the complex - taking into account the internal transfer price between companies - and automatically redistributes the flows when any unit has an outage/fluctuation."**

---

## 2. SRS Document – Dedicated product of Bandar Imam Petrochemical

### 2-1. Introduction
**Purpose:** Maximize the total gross margin of the Bandar Imam complex through real-time allocation of feedstock and shared utility capacity among the four subsidiaries, and automatic redistribution of intermediate streams when any unit has an outage/production fluctuation.

**Field challenges:**
- The decision "how much naphtha/NGL/methanol goes to which unit (NF→OL→AR/PX)" is usually made based on a fixed monthly plan, not on the instantaneous fluctuation of final product prices.
- When the OL cracker loses capacity, the allocation of ethylene/propylene between Bespar (HDPE/LDPE/PP) and Kimia (VCM/PVC) is usually done manually and with delay.
- Abniroo's steam/power/nitrogen capacity is a hidden constraint that is often accounted for late in the feedstock planning of the other 3 companies.
- There is no transparent internal-transfer-price model based on real data for fair decision-making among the 4 companies.

**Scope:** Bandar Imam complex, Mahshahr Petrochemical Special Economic Zone; connection to the DCS of the four subsidiaries and the inter-company settlement financial system.

### 2-2. General Requirements

| ID | Requirement | Priority |
| :--- | :--- | :--- |
| R-GEN-01 | Simultaneous reception of instantaneous production/capacity data from all 4 subsidiaries (Processing, Bespar, Kimia, Abniroo) | High |
| R-GEN-02 | Reception of instantaneous/daily final-product prices from the commodity exchange and export market | High |
| R-GEN-03 | Management dashboard "Complex command center" with an integrated view of margin, feedstock, and utility capacity of all 4 companies | High |
| R-GEN-04 | Connection to the inter-company settlement financial system to apply the internal transfer price | Medium |

### 2-3. Functional Requirements

| ID | Requirement | Patent capability |
| :--- | :--- | :--- |
| FR-ALLOC-01 | Optimization of feedstock (naphtha/NGL/methanol) allocation among processing units with the goal of maximizing the total margin of the complex | **Multi-company optimization with an internal transfer price (main innovation)** |
| FR-ALLOC-02 | Automatic reconfiguration of ethylene/propylene/butadiene flow between Bespar and Kimia when cracker capacity drops | Real-time redistribution of an intermediate stream among independent companies |
| FR-UTIL-01 | Modeling the shared utility capacity constraint (steam/power/nitrogen) of Abniroo as a direct constraint in feedstock allocation optimization | Linking shared utility to the feedstock decision of the other 3 companies |
| FR-MARGIN-01 | Estimation of the instantaneous gross margin of each process route (feedstock→final product) with ML based on market prices | Route profitability assessment with machine learning |
| FR-ALERT-01 | Alert and action recommendation upon a unit outage/fluctuation, computing the financial impact of alternative scenarios | Real-time financial-operational decision recommender |
| FR-LOOP-01 | Recording the actual result of each allocation decision (realized margin) for model retraining | Closed learning based on real financial outcome |

### 2-4. Non-Functional Requirements

| ID | Requirement | Target value |
| :--- | :--- | :--- |
| NFR-PER-01 | Recalculation delay of the optimal allocation after a price/capacity change | Less than 60 seconds |
| NFR-PER-02 | Accuracy of the instantaneous gross margin estimate | Less than 10% error relative to actual settlement |
| NFR-AVAIL-01 | System availability | 99.9% |
| NFR-SEC-01 | Separate RBAC for each of the 4 subsidiaries + senior complex manager; AES-256 encryption | Mandatory |

### 2-5. Technical Architecture

```
┌──────────────────┐
│   API Gateway     │ (RBAC + 2FA — shared holding pattern)
└─────────┬─────────┘
┌─────────┼─────────────────┬─────────────────┬───────────────┐
┌───▼───────────┐┌──────────▼────────┐┌────────▼────────┐┌────▼──────────┐
│Multi-Entity    ││ Margin Prediction ││ Feedstock/Utility││ Settlement/    │
│Ingestion       ││ (ML price+cost)   ││ MILP Optimizer   ││ Financial      │
│(4 subsidiaries ││                   ││ (NSGA-II/MILP)   ││ Connector      │
│ DCS + market)  ││                   ││                  ││ (ERP/Bourse)   │
└──────┬─────────┘└─────────┬─────────┘└────────┬─────────┘└───────┬────────┘
       └──────────┬─────────┴──────────┬────────┘                 │
                   ▼                    ▼                          │
            ┌────────────┐    ┌───────────────┐                    │
            │   Kafka    │    │  TimescaleDB   │                   │
            └────────────┘    └───────────────┘                    │
                                       │                            │
                                ┌────────────┐                      │
                                │   MLflow   │◄─────────────────────┘
                                └────────────┘
```

| Suggested path | Description |
| :--- | :--- |
| `services/multi-entity-ingestion/` | Connection to the DCS of all 4 subsidiaries + commodity exchange price feed |
| `services/margin-prediction/` | ML model for estimating the margin of each feedstock→product route |
| `services/feedstock-utility-optimizer/` | MILP solver with shared utility constraint |
| `services/settlement-connector/` | Connection to the inter-company settlement financial system |
| `shared/` | Reuse of products 1-4 |

---

## 3. Synthetic Data Generation Code

```python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

NUM_RECORDS = 10000
START_TIME = datetime(2026, 9, 14, 8, 0, 0)
timestamps = [START_TIME + timedelta(hours=i/60) for i in range(NUM_RECORDS)]
t = np.linspace(0, 20 * np.pi, NUM_RECORDS)

# instantaneous cracker (OL) capacity - percent of nominal capacity
cracker_capacity_percent = 92 + 5 * np.sin(t * 0.08) + np.random.normal(0, 2, NUM_RECORDS)
cracker_capacity_percent = np.clip(cracker_capacity_percent, 60, 100)

# instantaneous product prices (dollars per ton, simulated market fluctuation)
price_ethylene_usd_ton = 950 + 60 * np.sin(t * 0.03) + np.random.normal(0, 15, NUM_RECORDS)
price_hdpe_usd_ton = 1150 + 80 * np.sin(t * 0.025 + 1) + np.random.normal(0, 20, NUM_RECORDS)
price_pvc_usd_ton = 900 + 50 * np.sin(t * 0.02 + 2) + np.random.normal(0, 18, NUM_RECORDS)

# shared Abniroo utility capacity (% of available steam/power capacity)
utility_steam_available_percent = 88 + 6 * np.sin(t * 0.05) + np.random.normal(0, 3, NUM_RECORDS)
utility_power_available_percent = 90 + 4 * np.sin(t * 0.06 + 0.5) + np.random.normal(0, 2, NUM_RECORDS)

# feedstock allocation among units (simulation of the current optimal share)
naphtha_to_ol_percent = 70 + 10 * np.sin(t * 0.04) + np.random.normal(0, 3, NUM_RECORDS)
naphtha_to_ol_percent = np.clip(naphtha_to_ol_percent, 40, 90)

# estimated instantaneous gross margin of the entire complex (million dollars/day, simulated)
estimated_gross_margin_musd_day = (
    0.02 * cracker_capacity_percent
    + 0.015 * (price_ethylene_usd_ton - 900)
    + 0.01 * (price_hdpe_usd_ton - 1100)
    + 0.008 * (price_pvc_usd_ton - 880)
    - 0.01 * (100 - utility_steam_available_percent)
    + np.random.normal(0, 0.3, NUM_RECORDS)
)

# label: need for immediate reconfiguration of the intermediate stream (when cracker or utility capacity drops sharply)
needs_reallocation = ((cracker_capacity_percent < 75) | (utility_steam_available_percent < 75)).astype(int)

df = pd.DataFrame({
    'timestamp': timestamps,
    'cracker_capacity_percent': np.round(cracker_capacity_percent, 2),
    'price_ethylene_usd_ton': np.round(price_ethylene_usd_ton, 1),
    'price_hdpe_usd_ton': np.round(price_hdpe_usd_ton, 1),
    'price_pvc_usd_ton': np.round(price_pvc_usd_ton, 1),
    'utility_steam_available_percent': np.round(utility_steam_available_percent, 2),
    'utility_power_available_percent': np.round(utility_power_available_percent, 2),
    'naphtha_to_ol_percent': np.round(naphtha_to_ol_percent, 2),
    'estimated_gross_margin_musd_day': np.round(estimated_gross_margin_musd_day, 3),
    'needs_reallocation': needs_reallocation,
})

df.to_csv("bipc_multiplant_margin_data_10k.csv", index=False)
print(f"✅ Saved. Records: {len(df):,} - Variables: {len(df.columns)}")
print(df.describe())
```

---

## 4. Economic Justification

| Indicator | Current state | With Khalij-BIMO | Approximate financial impact |
| :--- | :--- | :--- | :--- |
| Feedstock allocation among units | Fixed monthly plan, late reaction to price fluctuation | Real-time reallocation based on instantaneous margin | A multi-percent improvement in gross margin on the 4,748 kilotons/year product turnover |
| Response to cracker outage | Manual decision to reconfigure flow among subsidiaries, usually with hours of delay | Automatic reconfiguration in less than one minute | Reduced downstream (Bespar/Kimia) downtime caused by feedstock shortage |
| Shared utility productivity | Steam/power limits are often accounted for late in feedstock planning | The utility constraint is included from the start in feedstock optimization | Reduced risk of unexpected production limitation |

**Payback:** Given the scale of Iran's largest petrochemical complex (4,748 kilotons/year), even a 0.5-1% improvement in the total gross margin of the complex through optimal feedstock allocation has an annual economic value of several million dollars, which quickly offsets the implementation cost.

---

## 5. Proposed Evolution Roadmap (Phase 1-7)

| Phase | Capability |
| :--- | :--- |
| 1 | Base infrastructure + data simulator + Kafka/TimescaleDB connection shared with product 1 |
| 2 | ML model for estimating the gross margin of each feedstock→product route |
| 3 | MILP feedstock allocation optimizer with shared utility constraint |
| 4 | Automatic reconfiguration of the intermediate stream among the 4 subsidiaries during outage/fluctuation |
| 5 | Connection to the inter-company settlement financial system and internal transfer price |
| 6 | "Complex command center" dashboard for the BIPC CEO |
| 7 | Operational pilot on a real OL cracker capacity-drop scenario |

---

## 6. Summary of Patentable Innovations

1. **Multi-company optimization of feedstock and intermediate stream** among 4 legally independent subsidiaries of a complex, with an internal transfer price.
2. **Direct linking of the shared utility capacity constraint** (steam/power/nitrogen) to the feedstock allocation decision of the other companies in a single model.
3. **Automatic real-time reconfiguration of intermediate streams** among companies during an outage/fluctuation with computation of the scenario's financial impact.

---

## 7. References

- [PGPIC — Bandar Imam Petrochemical Company](https://pgpic.ir/%D8%B4%D8%B1%DA%A9%D8%AA-%D9%87%D8%A7%DB%8C-%D8%AA%D8%A7%D8%A8%D8%B9%D9%87/%D9%85%D8%AC%D8%AA%D9%85%D8%B9-%D9%87%D8%A7%DB%8C-%D8%AA%D9%88%D9%84%DB%8C%D8%AF%DB%8C/%D8%B4%D8%B1%DA%A9%D8%AA-%D9%BE%D8%AA%D8%B1%D9%88%D8%B4%DB%8C%D9%85%DB%8C-%D8%A8%D9%86%D8%AF%D8%B1-%D8%A7%D9%85%D8%A7%D9%85)
- [BIPC — Products](https://bipc.ir/en/products/)
- [Persian Wikipedia — Bandar Imam Petrochemical Company](https://fa.wikipedia.org/wiki/%D8%B4%D8%B1%DA%A9%D8%AA_%D9%BE%D8%AA%D8%B1%D9%88%D8%B4%DB%8C%D9%85%DB%8C_%D8%A8%D9%86%D8%AF%D8%B1_%D8%A7%D9%85%D8%A7%D9%85)
- [US11663546B2 — Automated evaluation of refinery and petrochemical feedstocks using ML](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11663546)
- [US11886157B2 — Operational optimization of industrial steam and power utility systems](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11886157)
- [Mu Sigma — AI-Driven S&OP Digital Transformation for a Global Petrochemical Leader](https://www.mu-sigma.com/case-study/ai-driven-sop-digital-transformation-for-a-global-petrochemical-leader/)
- [Integrated model of refining and petrochemical plant for enterprise-wide optimization — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0098135416303684)
