"""Write the synthetic multi-plant dataset: python scripts/generate_data.py [n_records] [out.csv]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from khalij_bimo.simulator import generate_history  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
out = sys.argv[2] if len(sys.argv) > 2 else "bipc_multiplant_margin_data_10k.csv"
df = generate_history(n)
df.to_csv(out, index=False)
print(f"Saved {len(df):,} records x {len(df.columns)} variables -> {out}")
