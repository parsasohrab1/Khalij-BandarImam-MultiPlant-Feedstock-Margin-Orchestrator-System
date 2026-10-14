"""Complex topology and technical coefficients.

ALL numbers here are illustrative placeholders (order-of-magnitude, consistent with the SRS).
They must be calibrated against real DCS / lab / settlement data before operational use.
"""
from __future__ import annotations

PROCESSING, BESPAR, KIMIA, ABNIROO = "processing", "bespar", "kimia", "abniroo"
COMPANIES = (PROCESSING, BESPAR, KIMIA, ABNIROO)

# Base market prices, USD/t
BASE_PRICES = {
    "naphtha": 620.0, "ngl": 380.0, "methanol": 330.0, "fuel": 450.0,
    "ethylene": 950.0, "propylene": 900.0, "c4": 800.0, "btx": 980.0,
    "hdpe": 1150.0, "ldpe": 1250.0, "pp": 1100.0, "sr": 1900.0,
    "pvc": 900.0, "mtbe": 750.0,
}
EXPORT_DISCOUNT = 0.04  # haircut when selling an intermediate on the spot/export market

# Nominal capacities (t/h of the stated stream) and supply limits
CAPACITY = {
    "ol_feed": 175.0, "ar_feed": 60.0,
    "hdpe": 20.0, "ldpe": 12.0, "pp": 14.0, "sr": 4.0, "pvc": 45.0, "mtbe": 6.0,
}
SUPPLY = {"naphtha": 240.0, "ngl": 40.0, "methanol": 6.0}
EXPORT_CAP = {"ethylene": 25.0, "propylene": 15.0, "c4": 8.0}

# Shared Abniroo utilities (nominal): steam t/h, power MW, nitrogen Nm3/h
UTILITY_CAPACITY = {"steam": 250.0, "power": 80.0, "n2": 12000.0}
UTILITY_TARIFF = {"steam": 22.0, "power": 55.0, "n2": 0.04}     # USD per unit, charged to consumers
UTILITY_COST = {"steam": 17.0, "power": 40.0, "n2": 0.025}      # Abniroo generation cost

# Yields (t product per t feed)
OL_YIELD_NAPHTHA = {"ethylene": 0.30, "propylene": 0.16, "c4": 0.09, "fuel": 0.45}
OL_YIELD_NGL = {"ethylene": 0.45, "propylene": 0.12, "c4": 0.04, "fuel": 0.39}
BTX_YIELD = 0.55
HDPE_YIELD, LDPE_YIELD, PP_YIELD, SR_YIELD = 0.99, 0.98, 0.98, 0.90
PVC_PER_ETHYLENE = 1.95
MTBE_C4, MTBE_METHANOL = 0.45, 0.55  # t per t MTBE

# Variable operating cost, USD per t of the unit's main throughput
OPEX = {"ol": 35.0, "ar": 30.0, "hdpe": 60.0, "ldpe": 85.0, "pp": 70.0, "sr": 250.0,
        "pvc": 330.0, "mtbe": 60.0}

# Specific utility use per t of throughput: (steam t, power MWh, N2 Nm3)
UTILITY_USE = {
    "ol": (1.00, 0.08, 20.0), "ar": (0.60, 0.05, 10.0),
    "hdpe": (0.15, 0.35, 40.0), "ldpe": (0.20, 0.50, 60.0), "pp": (0.15, 0.30, 40.0),
    "sr": (0.50, 0.25, 30.0), "pvc": (0.90, 0.90, 15.0), "mtbe": (0.40, 0.05, 5.0),
}

# Default internal transfer price policy: fraction of the external market price
TRANSFER_PRICE_FRACTION = {"ethylene": 0.97, "propylene": 0.97, "c4": 0.97}
