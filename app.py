from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from rent_engine import (
    REQUIRED_COLUMNS, HISTORY_COLUMNS, normalize_columns, clean_neighborhoods,
    clean_history, score_affordability, build_summary, quality_report,
    stress_band
)

st.set_page_config(
    page_title="RentRelief • Rental Affordability Stress Mapper",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
HERO = ROOT / "assets" / "rentrelief_hero.svg"

def css():
    st.markdown("""
    <style>
    .stApp {background:linear-gradient(180deg,#f7fbff 0%,#f4f8fc 55%,#eef6f4 100%);}
    .block-container {max-width:1480px;padding-top:1rem;padding-bottom:2rem;}
    [data-testid="stSidebar"] {background:#f8fbfd;border-right:1px solid #dbe7ef;}
    .hero {border:1px solid #d8e6ee;border-radius:26px;padding:24px 28px;
           background:linear-gradient(120deg,#ffffff 0%,#eef9f8 50%,#eff3ff 100%);
           box-shadow:0 14px 44px rgba(31,65,93,.08);margin-bottom:18px;}
    .hero h1 {margin:0;color:#18334b;font-size:2.35rem;letter-spacing:-.04em;}
    .hero p {color:#5d7184;margin:.28rem 0;font-size:1rem;}
    .badge {display:inline-block;padding:5px 11px;border-radius:999px;
            background:#dff6f2;color:#117d76;font-weight:800;font-size:.76rem;margin-bottom:8px;}
    .metric {background:#fff;border:1px solid #dce8ef;border-radius:18px;padding:16px 18px;
             box-shadow:0 7px 22px rgba(31,65,93,.06);min-height:112px;}
    .label {color:#667b8e;font-size:.75rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;}
    .value {color:#18334b;font-size:1.8rem;font-weight:900;margin-top:5px;}
    .sub {color:#718395;font-size:.8rem;margin-top:5px;}
    .section {font-size:1.18rem;font-weight:850;color:#18334b;margin:18px 0 8px;}
    .note {font-size:.82rem;color:#61788a;}
    </style>
    """, unsafe_allow_html=True)

def metric(label, value, sub):
    st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)

def gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=float(score),
        number={"font":{"size":42,"color":"#18334b"},"suffix":"/100"},
        gauge={"axis":{"range":[0,100],"tickcolor":"#91a5b5"},
               "bar":{"color":"#e97575","thickness":.28},
               "bgcolor":"#edf3f7","borderwidth":0,
               "steps":[{"range":[0,25],"color":"#dff7f1"},
                        {"range":[25,50],"color":"#e9f2ff"},
                        {"range":[50,75],"color":"#fff1d8"},
                        {"range":[75,100],"color":"#ffe4e6"}]}
    ))
    fig.update_layout(height=260,margin=dict(l=20,r=20,t=10,b=5),paper_bgcolor="white")
    return fig

@st.cache_data
def load_default():
    n = pd.read_csv(DATA/"sample_neighborhoods.csv")
    h = pd.read_csv(DATA/"sample_cost_history.csv")
    return n, h

def main():
    css()
    st.markdown("""
    <div class="hero">
      <div class="badge">LOCAL-FIRST • RENTRELIEF</div>
      <h1>Rental Affordability Stress Mapper</h1>
      <p>Transparent screening of neighborhood housing-cost pressure using rent, utilities, commuting costs, income, and recent trends.</p>
      <p class="note">Planning and decision-support only. Scores are not individual affordability determinations, eligibility decisions, or legal/financial advice.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## RentRelief")
        st.caption("Local CSV analytics • no external APIs")
        page = st.radio("Workspace",[
            "Command Center","Neighborhood Atlas","Neighborhood Deep Dive",
            "Cost Pressure","Income & Commute","Scenario Lab","Data Quality","Reports"
        ])
        st.divider()
        st.markdown("### Optional data")
        upload_n = st.file_uploader("Neighborhood metrics CSV",type=["csv"])
        upload_h = st.file_uploader("Cost history CSV",type=["csv"])
        st.caption("Required schemas are documented in `doc/DATA_DICTIONARY.md`.")

    neighborhoods, history = load_default()

    if upload_n is not None:
        try:
            neighborhoods = clean_neighborhoods(pd.read_csv(upload_n))
            st.sidebar.success("Neighborhood dataset loaded.")
        except Exception as e:
            st.sidebar.error(str(e))
    if upload_h is not None:
        try:
            history = clean_history(pd.read_csv(upload_h))
            st.sidebar.success("History dataset loaded.")
        except Exception as e:
            st.sidebar.error(str(e))

    scored = score_affordability(neighborhoods)
    hist = clean_history(history)
    summary = build_summary(scored)
    quality = quality_report(neighborhoods)

    if page == "Command Center":
        a,b,c,d,e = st.columns(5)
        with a: metric("Neighborhoods",summary["count"],"mapped records")
        with b: metric("High / critical",summary["high_critical"],"review queue")
        with c: metric("Average stress",f'{summary["avg_score"]:.1f}',"0–100 screening")
        with d: metric("Median rent burden",f'{summary["median_burden"]:.1f}%',"rent / income")
        with e: metric("Median total burden",f'{summary["median_total"]:.1f}%',"housing + commute")

        st.markdown('<div class="section">Affordability pressure landscape</div>',unsafe_allow_html=True)
        l,r = st.columns([1.55,1])
        with l:
            fig = px.scatter(scored,x="rent_burden_pct",y="stress_score",size="population",
                color="stress_band",hover_name="neighborhood_name",
                custom_data=["neighborhood_id","utility_burden_pct","commute_burden_pct","income_change_pct"],
                labels={"rent_burden_pct":"Rent burden (%)","stress_score":"Stress score"})
            fig.update_layout(height=430,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor="white")
            st.plotly_chart(fig,use_container_width=True)
        with r:
            dist=scored["stress_band"].value_counts().rename_axis("stress_band").reset_index(name="neighborhoods")
            fig2=px.bar(dist,x="stress_band",y="neighborhoods",color="stress_band",text_auto=True)
            fig2.update_layout(height=300,margin=dict(l=8,r=8,t=10,b=10),paper_bgcolor="white",showlegend=False)
            st.plotly_chart(fig2,use_container_width=True)
            st.markdown('<div class="note">Higher scores highlight combinations of local housing-cost signals that may justify deeper review.</div>',unsafe_allow_html=True)

        st.markdown('<div class="section">Priority neighborhoods</div>',unsafe_allow_html=True)
        cols=["neighborhood_id","neighborhood_name","stress_band","stress_score","rent_burden_pct","utility_burden_pct","commute_burden_pct","income_change_pct"]
        st.dataframe(scored.sort_values("stress_score",ascending=False)[cols],use_container_width=True,hide_index=True)

    elif page == "Neighborhood Atlas":
        st.markdown('<div class="section">Neighborhood affordability atlas</div>',unsafe_allow_html=True)
        fig=px.scatter_mapbox(scored,lat="latitude",lon="longitude",color="stress_score",size="population",
            hover_name="neighborhood_name",zoom=10,height=600,
            mapbox_style="open-street-map",
            color_continuous_scale=["#19a974","#ffd166","#ef767a"],
            labels={"stress_score":"Stress"})
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(scored[["neighborhood_id","neighborhood_name","zone","latitude","longitude","stress_score","stress_band"]].sort_values("stress_score",ascending=False),use_container_width=True,hide_index=True)

    elif page == "Neighborhood Deep Dive":
        selected=st.selectbox("Select neighborhood",scored["neighborhood_id"].tolist())
        row=scored[scored["neighborhood_id"]==selected].iloc[0]
        a,b=st.columns([.9,1.4])
        with a:
            st.markdown(f"### {row['neighborhood_name']}")
            st.caption(f"{row['neighborhood_id']} • {row['zone']}")
            st.plotly_chart(gauge(row["stress_score"]),use_container_width=True)
            st.markdown(f"**Stress band:** {row['stress_band']}")
            st.markdown("**Leading pressure signals**")
            for x in row["top_drivers"].split(" | "):
                st.markdown(f"• {x}")
        with b:
            items=pd.DataFrame({
                "Signal":["Rent burden","Utilities burden","Commute burden","Income change","Rent growth"],
                "Value":[row["rent_burden_pct"],row["utility_burden_pct"],row["commute_burden_pct"],row["income_change_pct"],row["rent_growth_pct"]]
            })
            fig=px.bar(items,x="Signal",y="Value",text_auto=".1f")
            fig.update_layout(height=360,margin=dict(l=10,r=10,t=12,b=18),paper_bgcolor="white")
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(row.to_frame("Value"),use_container_width=True)

        h=hist[hist["neighborhood_id"].astype(str)==str(selected)].sort_values("period")
        st.markdown('<div class="section">Cost history</div>',unsafe_allow_html=True)
        if h.empty:
            st.info("No history records found for this neighborhood.")
        else:
            fig=px.line(h,x="period",y=["monthly_rent","monthly_utilities","monthly_commute_cost","monthly_income"],markers=True)
            fig.update_layout(height=350,paper_bgcolor="white",margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)

    elif page == "Cost Pressure":
        a,b=st.columns(2)
        with a:
            fig=px.bar(scored.sort_values("rent_burden_pct"),x="rent_burden_pct",y="neighborhood_name",orientation="h",
                       color="stress_score",color_continuous_scale=["#65c18c","#ffd166","#ef767a"])
            fig.update_layout(height=520,paper_bgcolor="white",margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
        with b:
            fig=px.scatter(scored,x="monthly_rent",y="monthly_utilities",size="population",color="stress_band",hover_name="neighborhood_name")
            fig.update_layout(height=520,paper_bgcolor="white",margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
        st.dataframe(scored[["neighborhood_id","neighborhood_name","monthly_rent","monthly_utilities","rent_burden_pct","utility_burden_pct","stress_score","stress_band"]].sort_values("stress_score",ascending=False),use_container_width=True,hide_index=True)

    elif page == "Income & Commute":
        a,b=st.columns(2)
        with a:
            fig=px.scatter(scored,x="income_change_pct",y="commute_burden_pct",size="population",color="stress_band",hover_name="neighborhood_name")
            fig.add_vline(x=0,line_dash="dash",line_color="#8093a6")
            fig.update_layout(height=430,paper_bgcolor="white",margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
        with b:
            fig=px.scatter(scored,x="average_commute_minutes",y="commute_cost_share_pct",size="population",color="stress_band",hover_name="neighborhood_name")
            fig.update_layout(height=430,paper_bgcolor="white",margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
        st.dataframe(scored[["neighborhood_id","neighborhood_name","median_monthly_income","income_change_pct","monthly_commute_cost","commute_burden_pct","average_commute_minutes","stress_score"]].sort_values("stress_score",ascending=False),use_container_width=True,hide_index=True)

    elif page == "Scenario Lab":
        st.markdown('<div class="section">Housing-cost what-if lab</div>',unsafe_allow_html=True)
        choice=st.selectbox("Neighborhood",scored["neighborhood_id"].tolist())
        base=scored[scored["neighborhood_id"]==choice].iloc[0]
        c1,c2,c3,c4=st.columns(4)
        with c1: rent_delta=st.slider("Rent change (%)",-25,35,0)
        with c2: utility_delta=st.slider("Utility change (%)",-25,30,0)
        with c3: commute_delta=st.slider("Commute-cost change (%)",-30,35,0)
        with c4: income_delta=st.slider("Income change (%)",-20,25,0)
        rent=max(base["monthly_rent"]*(1+rent_delta/100),1)
        utility=max(base["monthly_utilities"]*(1+utility_delta/100),0)
        commute=max(base["monthly_commute_cost"]*(1+commute_delta/100),0)
        income=max(base["median_monthly_income"]*(1+income_delta/100),1)
        rent_b=rent/income*100
        util_b=utility/income*100
        comm_b=commute/income*100
        total=(rent+utility+commute)/income*100
        scenario=float(np.clip(
            rent_b*0.38 + util_b*0.14 + comm_b*0.18 +
            np.clip(-income_delta,0,100)*0.45 + max(0,base["rent_growth_pct"])*0.9 +
            np.clip(total-30,0,70)*0.8,0,100
        ))
        l,r=st.columns([.9,1.1])
        with l: st.plotly_chart(gauge(scenario),use_container_width=True)
        with r:
            st.metric("Baseline score",f'{base["stress_score"]:.1f}')
            st.metric("Scenario score",f"{scenario:.1f}")
            st.metric("Scenario total cost burden",f"{total:.1f}%")
            st.write(f"**Scenario band:** {stress_band(scenario)}")
            st.caption("Directional screening only; not an affordability eligibility or financial advice tool.")

    elif page == "Data Quality":
        a,b,c=st.columns(3)
        with a: metric("Rows",quality["rows"],"neighborhood records")
        with b: metric("Missing cells",quality["missing_cells"],"required fields")
        with c: metric("Duplicate IDs",quality["duplicate_ids"],"must be 0")
        st.dataframe(pd.DataFrame(quality["columns"]),use_container_width=True,hide_index=True)
        st.markdown('<div class="section">Required schema</div>',unsafe_allow_html=True)
        st.code("\n".join(REQUIRED_COLUMNS))

    elif page == "Reports":
        report=scored[["neighborhood_id","neighborhood_name","stress_band","stress_score","rent_burden_pct","utility_burden_pct","commute_burden_pct","income_change_pct","top_drivers"]].sort_values("stress_score",ascending=False)
        st.markdown('<div class="section">Review-ready screening report</div>',unsafe_allow_html=True)
        st.dataframe(report,use_container_width=True,hide_index=True)
        st.download_button("Download screening summary CSV",report.to_csv(index=False).encode(),file_name="rentrelief_screening_summary.csv",mime="text/csv")

if __name__ == "__main__":
    main()
