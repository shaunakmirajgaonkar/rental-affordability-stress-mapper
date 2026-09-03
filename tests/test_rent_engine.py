from pathlib import Path
import pandas as pd
import pytest
from rent_engine import REQUIRED_COLUMNS, clean_neighborhoods, clean_history, score_affordability, normalize_column

ROOT=Path(__file__).resolve().parents[1]

def test_schema_and_unique_ids():
    df=pd.read_csv(ROOT/"data/sample_neighborhoods.csv")
    clean=clean_neighborhoods(df)
    assert clean.columns.tolist()==REQUIRED_COLUMNS
    assert clean["neighborhood_id"].is_unique

def test_history_allows_repeated_ids():
    h=clean_history(pd.read_csv(ROOT/"data/sample_cost_history.csv"))
    assert h["neighborhood_id"].duplicated().any()

def test_score_bounded():
    s=score_affordability(clean_neighborhoods(pd.read_csv(ROOT/"data/sample_neighborhoods.csv")))
    assert s["stress_score"].between(0,100).all()
    assert set(s["stress_band"]).issubset({"Low","Moderate","High","Critical"})

def test_duplicate_primary_ids_rejected():
    df=pd.read_csv(ROOT/"data/sample_neighborhoods.csv")
    df.loc[1,"neighborhood_id"]=df.loc[0,"neighborhood_id"]
    with pytest.raises(ValueError,match="duplicate"):
        clean_neighborhoods(df)

def test_alias_normalization():
    assert normalize_column("Neighborhood ID")=="neighborhood_id"
    assert normalize_column("Median Income")=="median_monthly_income"
