from pathlib import Path
import pandas as pd
from rent_engine import REQUIRED_COLUMNS, clean_neighborhoods, clean_history, score_affordability
ROOT=Path(__file__).resolve().parent
n=clean_neighborhoods(pd.read_csv(ROOT/"data/sample_neighborhoods.csv"))
h=clean_history(pd.read_csv(ROOT/"data/sample_cost_history.csv"))
s=score_affordability(n)
assert list(n.columns)==REQUIRED_COLUMNS
assert n["neighborhood_id"].is_unique
assert s["stress_score"].between(0,100).all()
assert h["neighborhood_id"].duplicated().any()  # history is allowed to repeat IDs
print("PASS: RentRelief rental affordability screening")
print(f"Neighborhoods: {len(s)}")
print(f"Stress range: {s.stress_score.min():.1f}–{s.stress_score.max():.1f}")
print(f"High/Critical: {(s.stress_score>=50).sum()}")
