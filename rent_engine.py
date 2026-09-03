from __future__ import annotations
import re
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "neighborhood_id","neighborhood_name","zone","latitude","longitude","population",
    "median_monthly_income","income_change_pct","monthly_rent","rent_growth_pct",
    "monthly_utilities","monthly_commute_cost","average_commute_minutes"
]
HISTORY_COLUMNS = [
    "neighborhood_id","period","monthly_rent","monthly_utilities",
    "monthly_commute_cost","monthly_income"
]

ALIASES = {
    "neighborhood id":"neighborhood_id","neighborhood code":"neighborhood_id","area id":"neighborhood_id",
    "neighborhood name":"neighborhood_name","area name":"neighborhood_name",
    "income":"median_monthly_income","median income":"median_monthly_income",
    "income change":"income_change_pct","rent":"monthly_rent","rent growth":"rent_growth_pct",
    "utilities":"monthly_utilities","utility cost":"monthly_utilities",
    "commute cost":"monthly_commute_cost","commute minutes":"average_commute_minutes",
}
def normalize_column(name):
    x=re.sub(r"[^a-z0-9]+"," ",str(name).strip().lower()).strip()
    return ALIASES.get(x,x.replace(" ","_"))

def normalize_columns(df):
    out=df.copy()
    out.columns=[normalize_column(c) for c in out.columns]
    return out

def clean_neighborhoods(df):
    out=normalize_columns(df)
    missing=[c for c in REQUIRED_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError("Neighborhood CSV is missing required column(s): "+", ".join(missing))
    numeric=[c for c in REQUIRED_COLUMNS if c not in {"neighborhood_id","neighborhood_name","zone"}]
    for c in numeric: out[c]=pd.to_numeric(out[c],errors="coerce")
    out["neighborhood_id"]=out["neighborhood_id"].astype(str).str.strip()
    out["neighborhood_name"]=out["neighborhood_name"].astype(str).str.strip()
    if out["neighborhood_id"].duplicated().any():
        vals=", ".join(out.loc[out["neighborhood_id"].duplicated(),"neighborhood_id"].unique()[:8])
        raise ValueError("Neighborhood CSV has duplicate neighborhood_id values: "+vals)
    if out[REQUIRED_COLUMNS].isna().any().any():
        bad=out[REQUIRED_COLUMNS].isna().sum()
        bad=", ".join(f"{k}={v}" for k,v in bad.items() if v)
        raise ValueError("Neighborhood CSV has missing/invalid values: "+bad)
    return out[REQUIRED_COLUMNS].copy()

def clean_history(df):
    out=normalize_columns(df)
    missing=[c for c in HISTORY_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError("History CSV is missing required column(s): "+", ".join(missing))
    for c in HISTORY_COLUMNS:
        if c not in {"neighborhood_id","period"}: out[c]=pd.to_numeric(out[c],errors="coerce")
    out["neighborhood_id"]=out["neighborhood_id"].astype(str).str.strip()
    out["period"]=out["period"].astype(str)
    if out[HISTORY_COLUMNS].isna().any().any():
        raise ValueError("History CSV contains missing/invalid values in required fields.")
    return out[HISTORY_COLUMNS].copy()

def stress_band(score):
    if score < 25: return "Low"
    if score < 50: return "Moderate"
    if score < 75: return "High"
    return "Critical"

def score_affordability(df):
    out=df.copy()
    income=out["median_monthly_income"].replace(0,np.nan)
    out["rent_burden_pct"]=out["monthly_rent"]/income*100
    out["utility_burden_pct"]=out["monthly_utilities"]/income*100
    out["commute_burden_pct"]=out["monthly_commute_cost"]/income*100
    out["commute_cost_share_pct"]=out["monthly_commute_cost"]/income*100
    total=(out["monthly_rent"]+out["monthly_utilities"]+out["monthly_commute_cost"])/income*100

    rent_component=np.clip((out["rent_burden_pct"]-20)/35*100,0,100)
    utility_component=np.clip((out["utility_burden_pct"]-3)/12*100,0,100)
    commute_component=np.clip((out["commute_burden_pct"]-4)/14*100,0,100)
    income_component=np.clip((-out["income_change_pct"]+2)/15*100,0,100)
    growth_component=np.clip((out["rent_growth_pct"]-2)/10*100,0,100)
    total_component=np.clip((total-28)/45*100,0,100)

    out["stress_score"]=np.round(
        rent_component*0.31 + utility_component*0.12 + commute_component*0.18 +
        income_component*0.14 + growth_component*0.10 + total_component*0.15,1
    )
    out["stress_band"]=out["stress_score"].map(stress_band)

    drivers=[]
    for _,r in out.iterrows():
        parts=[]
        if r["rent_burden_pct"]>=30: parts.append(f"rent burden {r['rent_burden_pct']:.1f}%")
        if r["utility_burden_pct"]>=6: parts.append(f"utility burden {r['utility_burden_pct']:.1f}%")
        if r["commute_burden_pct"]>=8: parts.append(f"commute burden {r['commute_burden_pct']:.1f}%")
        if r["income_change_pct"]<0: parts.append(f"income trend {r['income_change_pct']:.1f}%")
        if r["rent_growth_pct"]>=5: parts.append(f"rent growth {r['rent_growth_pct']:.1f}%")
        if total.loc[r.name]>=35: parts.append(f"total cost burden {total.loc[r.name]:.1f}%")
        drivers.append(" | ".join(parts[:4]) if parts else "no dominant screen-level driver")
    out["top_drivers"]=drivers
    return out

def build_summary(df):
    return {
        "count":int(len(df)),
        "high_critical":int((df["stress_score"]>=50).sum()),
        "avg_score":float(df["stress_score"].mean()),
        "median_burden":float(df["rent_burden_pct"].median()),
        "median_total":float(((df["monthly_rent"]+df["monthly_utilities"]+df["monthly_commute_cost"])/df["median_monthly_income"]*100).median())
    }

def quality_report(df):
    normalized=normalize_columns(df)
    columns=[]
    for c in REQUIRED_COLUMNS:
        columns.append({"column":c,"present":c in normalized.columns,
                        "missing_values":int(normalized[c].isna().sum()) if c in normalized.columns else None})
    dup=int(normalized["neighborhood_id"].duplicated().sum()) if "neighborhood_id" in normalized.columns else 0
    return {"rows":int(len(df)),"missing_cells":int(normalized[[c for c in REQUIRED_COLUMNS if c in normalized.columns]].isna().sum().sum()),
            "duplicate_ids":dup,"columns":columns}
