
import sys
import streamlit as st
sys.path.append("..")
from password import login_required
login_required() 
import pandas as pd 
import plotly.express as px
from filter import sidebar_filters

st.set_page_config(page_title="9-Month Forecast", layout="wide")

# =====================================================
# CONFIG
# =====================================================
import os

# =====================================================
# CONFIG
# =====================================================
BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "sales_data3.xlsx")

TARGET_CUSTOMERS = [
    "TechnipFMC Norge AS (KOS1)",
    "TECHNIPFMC INDUSTRIES-SOLE PROPRIETORSHIP L.L.C. (7042)",
    "TechnipFMC Canada Ltd (EWOD)",
    "TechnipFMC Services Australia Ltd (EWAA)",
    "TechnipFMC do Brasil Ltda (REMS - ESPB - Fassub)",
    "TechnipFMC do Brasil Ltda (Macaé - EWBO)",
    "TechnipFMC do Brasil Ltda (Fassub - EWBO)",
    "TechnipFMC Services Australia Ltd (SFVA)",
    "Stream-Flo Edmonton",
    "Stream-Flo USA LLC",
    "QUEST SEALING SOLUTION"
]

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE, engine="openpyxl")
    df.columns = df.columns.str.strip()

    df["Customer"] = df["Customer"].astype(str).str.strip()
    df["Cleaned PO Date"] = pd.to_datetime(df["Cleaned PO Date"], errors="coerce")

    df["Sales"] = pd.to_numeric(df["Product value INR"], errors="coerce").fillna(0)
    df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(0)

    df["Month"] = df["Cleaned PO Date"].dt.to_period("M").dt.to_timestamp()
    df["Month_No"] = df["Month"].dt.month
    df["Year"] = df["Month"].dt.year

    return df.dropna(subset=["Cleaned PO Date"])

df = load_data()

# =====================================================
# 🔒 MASK CUSTOMER NAME
# =====================================================
MASK_CUSTOMER_NAME = "KLINGER LIMITED"
df["Customer"] = df["Customer"].replace({MASK_CUSTOMER_NAME: "Demo"})
if "Demo" not in TARGET_CUSTOMERS:
    TARGET_CUSTOMERS.append("Demo")

df = df[df["Customer"].isin(TARGET_CUSTOMERS)]

# =====================================================
# GLOBAL FILTERS
# =====================================================
customers, start_date, end_date, months = sidebar_filters(df)

df = df[
    (df["Customer"].isin(customers)) &
    (df["Cleaned PO Date"].dt.date >= start_date) &
    (df["Cleaned PO Date"].dt.date <= end_date)
]

if df.empty:
    st.warning("⚠️ No data available for selected filters")
    st.stop()

# =====================================================
# HEADER
# =====================================================
st.title(" Demand Forecast – Strategic")
st.caption("Explainable forecast using same-month-last-year + recent demand trend")

# =====================================================
# FORECAST ENGINE
# =====================================================
def forecast_top5(df, group_cols, value_col, months_ahead=9):

    hist = (
        df.groupby(group_cols + ["Year", "Month_No"])
        .agg(Value=(value_col, "sum"))
        .reset_index()
    )

    last_month = df["Month"].max()
    current_year = last_month.year

    recent_avg = hist[hist["Year"] == current_year]["Value"].mean()
    last_year_avg = hist[hist["Year"] == current_year - 1]["Value"].mean()
    growth = recent_avg / last_year_avg if last_year_avg and last_year_avg > 0 else 1.0

    rows = []

    for i in range(1, months_ahead + 1):
        future_month = last_month + pd.DateOffset(months=i)
        m_no = future_month.month

        base = hist[
            (hist["Year"] == current_year - 1) &
            (hist["Month_No"] == m_no)
        ].copy()

        if base.empty:
            continue

        base["Forecast"] = (base["Value"] * growth).round(0)
        base["Month"] = future_month

        rows.append(base.sort_values("Forecast", ascending=False).head(5))

    return pd.concat(rows) if rows else pd.DataFrame()

# =====================================================
# MONTHLY SECTION
# =====================================================
def render_section(title, group_cols):

    st.markdown(f"## {title}")
    tab_sales, tab_qty = st.tabs([" Sales", " Quantity"])

    for tab, col, symbol in zip([tab_sales, tab_qty], ["Sales", "Qty"], ["₹", ""]):
        with tab:
            fc = forecast_top5(df, group_cols, col)
            if fc.empty:
                st.warning("Not enough data")
                return

            fc["Month_Label"] = fc["Month"].dt.strftime("%b %Y")
            fc["Label"] = (
                fc[group_cols].astype(str).agg(" | ".join, axis=1)
                if group_cols else "Overall"
            )

            # 🔥 STRICT PER-MONTH SORT
            fc = (
                fc.sort_values(["Month", "Forecast"], ascending=[True, False])
                .groupby("Month", group_keys=False)
                .apply(lambda x: x.sort_values("Forecast", ascending=False))
            )

            fc["Bar_Text"] = fc["Label"] + "<br>" + symbol + fc["Forecast"].map(lambda x: f"{x:,.0f}")

            label_order = (
                fc.groupby("Label")["Forecast"]
                .sum().sort_values(ascending=False).index.tolist()
            )

            fig = px.bar(
                fc,
                x="Month_Label",
                y="Forecast",
                color="Label",
                barmode="stack",
                text="Bar_Text",
                category_orders={"Label": label_order},
                title=f"Top-5 {title} – {col} Forecast"
            )

            fig.update_traces(textposition="inside", textfont=dict(color="white", size=11))
            fig.update_layout(showlegend=True, bargap=0.15)

            st.plotly_chart(fig, use_container_width=True)
         # ===============================
#             # ✅ CORRECT BUSINESS SUMMARY
#             # ===============================
            summary = (
                fc.groupby("Month_Label", as_index=False)
                .agg(Total=("Forecast", "sum"))
            )

            peak = summary.loc[summary["Total"].idxmax()]
            low = summary.loc[summary["Total"].idxmin()]

            st.info(f"""
**Business Insight**
- Forecast uses **same month last year**
- Adjusted by **recent demand trend**
- **Peak Month:** {peak['Month_Label']} ({symbol}{peak['Total']:,.0f})
- **Lowest Month:** {low['Month_Label']} ({symbol}{low['Total']:,.0f})
""")
# =====================================================
# QUARTERLY SECTION (🔥 FIXED ORDER)
# =====================================================
def render_quarterly_section(title, group_cols):

    st.markdown(f"##  Quarterly Forecast – {title}")
    tab_sales, tab_qty = st.tabs([" Sales", " Quantity"])

    for tab, col, symbol in zip([tab_sales, tab_qty], ["Sales", "Qty"], ["₹", ""]):
        with tab:
            fc = forecast_top5(df, group_cols, col)
            if fc.empty:
                st.warning("Not enough data")
                return

            fc["Quarter"] = fc["Month"].dt.to_period("Q").astype(str)
            fc["Label"] = (
                fc[group_cols].astype(str).agg(" | ".join, axis=1)
                if group_cols else "Overall"
            )

            qtr_df = (
                fc.groupby(["Quarter", "Label"], as_index=False)
                .agg(Forecast=("Forecast", "sum"))
            )

            # 🔥 STRICT PER-QUARTER SORT
            qtr_df = (
                qtr_df.sort_values(["Quarter", "Forecast"], ascending=[True, False])
                .groupby("Quarter", group_keys=False)
                .apply(lambda x: x.sort_values("Forecast", ascending=False))
                .groupby("Quarter", group_keys=False)
                .head(5)
            )

            qtr_df["Bar_Text"] = qtr_df["Label"] + "<br>" + symbol + qtr_df["Forecast"].map(lambda x: f"{x:,.0f}")

            label_order = (
                qtr_df.groupby("Label")["Forecast"]
                .sum().sort_values(ascending=False).index.tolist()
            )

            fig = px.bar(
                qtr_df,
                x="Quarter",
                y="Forecast",
                color="Label",
                barmode="stack",
                text="Bar_Text",
                category_orders={"Label": label_order},
                title=f"{title} – Quarterly {col} Forecast"
            )

            fig.update_traces(textposition="inside", textfont=dict(color="white", size=11))
            fig.update_layout(showlegend=True, bargap=0.2)

            st.plotly_chart(fig, use_container_width=True)
            
            # Business insight
            q_sum = qtr_df.groupby("Quarter", as_index=False)["Forecast"].sum()
            peak = q_sum.loc[q_sum["Forecast"].idxmax()]
            low = q_sum.loc[q_sum["Forecast"].idxmin()]

            st.info(f"""
**Quarterly Business Insight**
- **Highest quarter:** {peak['Quarter']} ({symbol}{peak['Forecast']:,.0f})
- **Lowest quarter:** {low['Quarter']} ({symbol}{low['Forecast']:,.0f})
- Helps planning **capacity & commitments**
""")
# =====================================================
# DASHBOARD SECTIONS
# =====================================================
render_section("Overall", [])
render_section("Ring", ["Ring"])
render_section("Material", ["Material"])
render_section("Ring + Material", ["Ring", "Material"])

render_quarterly_section("Overall", [])
render_quarterly_section("Ring", ["Ring"])
render_quarterly_section("Material", ["Material"])
render_quarterly_section("Ring + Material", ["Ring", "Material"])
