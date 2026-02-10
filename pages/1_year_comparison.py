
import sys
import streamlit as st
sys.path.append("..")
from password import login_required
login_required() 
import pandas as pd
import plotly.express as px
from filter import sidebar_filters

st.set_page_config(page_title="Year Comparison", layout="wide")

# =====================================================
# CONFIG
# =====================================================
import os

# =====================================================
# CONFIG
# =====================================================
DATA_FILE = "Data.xlsx"


TARGET_CUSTOMERS = [
    "ABCD SOLUTION"
     "ALONE SOLUTION "
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
    df["Product value INR"] = pd.to_numeric(df["Product value INR"], errors="coerce").fillna(0)
    df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(0)
    df["Year"] = df["Cleaned PO Date"].dt.year
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
df["Year"] = df["Year"].astype(str)   # ✅ FORCE CATEGORICAL YEAR
# FINAL DATAFRAME USED EVERYWHERE
final_df = df.copy()
# =====================================================
# DERIVED MONTH COLUMNS (REQUIRED FOR ALL SUMMARIES)
# =====================================================
final_df["Month_Name"] = final_df["Cleaned PO Date"].dt.strftime("%b")
final_df["Month_No"] = final_df["Cleaned PO Date"].dt.month
final_df["Month_Period"] = (
    final_df["Cleaned PO Date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

if df.empty:
    st.warning("⚠️ No data found for selected filters")
    st.stop()
# selected_years = sorted(df["Year"].unique())
# year_text = ", ".join(selected_years)
selected_years = sorted(final_df["Year"].unique())
year_text = ", ".join(map(str, selected_years))

# =====================================================
# HEADER
# =====================================================
st.title(" Ring & Material – Year Comparison Dashboard")
st.caption(f"Period: {start_date} to {end_date}")

# =====================================================
# KPI SUMMARY
# =====================================================
kpi = df.groupby("Year").agg(
    Sales=("Product value INR", "sum"),
    Qty=("Qty", "sum"),
    Orders=("Qty", "count")
).reset_index()

st.dataframe(kpi, use_container_width=True)

# =====================================================
# 1️⃣ TOP RING (YEAR COMPARISON)
# =====================================================
st.markdown("## 1️ Top Ring")

tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])

ring_year = df.groupby(["Year", "Ring"]).agg(
    Sales=("Product value INR", "sum"),
    Qty=("Qty", "sum")
).reset_index()

with tab_sales:
    ring_year_sorted = ring_year.sort_values("Sales", ascending=False)

    fig = px.bar(
        ring_year_sorted,
        x="Ring",
        y="Sales",
        color="Year",
        title="Top Rings – Sales Comparison by Year",
        text="Sales"
    )

    fig.update_traces(
        texttemplate="₹%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.1
    )

    st.plotly_chart(fig, use_container_width=True)
with tab_qty:
    ring_year_sorted = ring_year.sort_values("Qty", ascending=False)

    fig = px.bar(
        ring_year_sorted,
        x="Ring",
        y="Qty",
        color="Year",
        title="Top Rings – Quantity Comparison by Year",
        text="Qty"
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.1
    )

    st.plotly_chart(fig, use_container_width=True)
# ================================
# 📌 TOP RING – YEAR-WISE BUSINESS INSIGHT
# ================================

st.markdown("###  Top Ring – Year-wise Business Insight")

for yr in selected_years:

    year_df = final_df[final_df["Year"] == yr]

    ring_year_ctx = (
        year_df.groupby("Ring")
        .agg(
            Sales=("Product value INR", "sum"),
            Qty=("Qty", "sum")
        )
        .sort_values("Sales", ascending=False)
        .reset_index()
    )

    if ring_year_ctx.empty:
        continue

    top_ring = ring_year_ctx.iloc[0]

    # Month behavior for this ring & year
    ring_month = (
        year_df[year_df["Ring"] == top_ring["Ring"]]
        .groupby("Month_Name")
        .agg(Sales=("Product value INR", "sum"))
        .reset_index()
    )

    peak_month = ring_month.sort_values("Sales", ascending=False).iloc[0]
    slow_month = ring_month.sort_values("Sales", ascending=True).iloc[0]

    st.info(f"""
### 📊 {yr} – Top Ring Performance

- **Top Ring:** {top_ring['Ring']}
- **Total Sales:** ₹{top_ring['Sales']:,.0f}
- **Total Quantity:** {top_ring['Qty']:,.0f} units

**Demand Timing**
- 🔼 Highest Month: **{peak_month['Month_Name']}** (₹{peak_month['Sales']:,.0f})
- 🔽 Lowest Month: **{slow_month['Month_Name']}** (₹{slow_month['Sales']:,.0f})
""")


# =====================================================
# 2️⃣ TOP MATERIAL (YEAR COMPARISON)
# =====================================================
st.markdown("## 2️ Top Material")

tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])

material_year = df.groupby(["Year", "Material"]).agg(
    Sales=("Product value INR", "sum"),
    Qty=("Qty", "sum")
).reset_index()

with tab_sales:
    material_sorted = material_year.sort_values("Sales", ascending=False)

    fig = px.bar(
        material_sorted,
        x="Material",
        y="Sales",
        color="Year",
        title="Top Materials – Sales Comparison by Year",
        text="Sales"
    )

    fig.update_traces(
        texttemplate="₹%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.1
    )

    st.plotly_chart(fig, use_container_width=True)
with tab_qty:
    material_sorted = material_year.sort_values("Qty", ascending=False)

    fig = px.bar(
        material_sorted,
        x="Material",
        y="Qty",
        color="Year",
        title="Top Materials – Quantity Comparison by Year",
        text="Qty"
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.1
    )

    st.plotly_chart(fig, use_container_width=True)
# ================================
# 📌 BUSINESS INSIGHT — TOP MATERIAL
# ================================
st.markdown("###  Top Material – Year-wise Business Insight")

for yr in selected_years:

    year_df = final_df[final_df["Year"] == yr]

    mat_ctx = (
        year_df.groupby("Material")
        .agg(
            Sales=("Product value INR", "sum"),
            Qty=("Qty", "sum")
        )
        .sort_values("Sales", ascending=False)
        .reset_index()
    )

    if mat_ctx.empty:
        continue

    top_mat = mat_ctx.iloc[0]

    st.info(f"""
### 📊 {yr} – Top Material Performance

- **Top Material:** {top_mat['Material']}
- **Sales Value:** ₹{top_mat['Sales']:,.0f}
- **Quantity:** {top_mat['Qty']:,.0f} units

This indicates **material standardization** during {yr}.
""")

# =====================================================
# 3️⃣ RING + MATERIAL (YEAR COMPARISON)
# =====================================================
st.markdown("## 3️ Ring + Material")

tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])

rm_year = df.groupby(["Year", "Ring", "Material"]).agg(
    Sales=("Product value INR", "sum"),
    Qty=("Qty", "sum")
).reset_index()

rm_year["Ring_Material"] = rm_year["Ring"] + " | " + rm_year["Material"]

with tab_sales:
    rm_sorted = rm_year.sort_values("Sales", ascending=False)

    fig = px.bar(
        rm_sorted,
        x="Ring_Material",
        y="Sales",
        color="Year",
        title="Ring + Material – Sales Comparison by Year",
        text="Sales"
    )

    fig.update_traces(
        texttemplate="₹%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        barmode="group",
        bargap=0.3,
        bargroupgap=0.15
    )

    st.plotly_chart(fig, use_container_width=True)
with tab_qty:
    rm_sorted = rm_year.sort_values("Qty", ascending=False)

    fig = px.bar(
        rm_sorted,
        x="Ring_Material",
        y="Qty",
        color="Year",
        title="Ring + Material – Quantity Comparison by Year",
        text="Qty"
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        barmode="group",
        bargap=0.3,
        bargroupgap=0.15
    )

    st.plotly_chart(fig, use_container_width=True)
# ================================
# 📌 BUSINESS INSIGHT — RING + MATERIAL
# ================================
st.markdown("###  Ring + Material – Year-wise Insight")

for yr in selected_years:

    year_df = final_df[final_df["Year"] == yr]

    rm_ctx = (
        year_df.groupby(["Ring", "Material"])
        .agg(
            Sales=("Product value INR", "sum"),
            Qty=("Qty", "sum")
        )
        .sort_values("Sales", ascending=False)
        .reset_index()
    )

    if rm_ctx.empty:
        continue

    top_rm = rm_ctx.iloc[0]

    st.info(f"""
### 📊 {yr} – Top Ring–Material Combination

- **Combination:** {top_rm['Ring']} | {top_rm['Material']}
- **Sales:** ₹{top_rm['Sales']:,.0f}
- **Quantity:** {top_rm['Qty']:,.0f} units

This combination shows **repeat procurement behavior** in {yr}.
""")

# =====================================================
# 4️⃣ MONTH-WISE TREND (YEAR COMPARISON)
# =====================================================
st.markdown("## 4️ Month-wise Trend")
tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])
df["Month_Name"] = df["Cleaned PO Date"].dt.strftime("%b")
df["Month_No"] = df["Cleaned PO Date"].dt.month

monthly_year = (
    df.groupby(["Year", "Month_No", "Month_Name"])
    .agg(Sales=("Product value INR", "sum"),
         Qty=("Qty", "sum"))
    .reset_index()
    .sort_values("Month_No")
)

with tab_sales:
    fig = px.line(
        monthly_year,
        x="Month_Name",
        y="Sales",
        color="Year",
        markers=True,
        title="Month-wise Sales Comparison by Year"
    )

    fig.update_traces(
        texttemplate="₹%{y:,.0f}",
        textposition="top center"
    )

    st.plotly_chart(fig, use_container_width=True)
with tab_qty:
    fig = px.line(
        monthly_year,
        x="Month_Name",
        y="Qty",
        color="Year",
        markers=True,
        title="Month-wise Quantity Comparison by Year"
    )

    fig.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="top center"
    )

    st.plotly_chart(fig, use_container_width=True)
# ================================
# 📌 BUSINESS INSIGHT — MONTHLY TREND
# ================================
st.markdown("###  Month-wise Demand Insight")

for yr in selected_years:

    yr_month = monthly_year[monthly_year["Year"] == yr]

    peak = yr_month.sort_values("Sales", ascending=False).iloc[0]
    slow = yr_month.sort_values("Sales", ascending=True).iloc[0]

    st.info(f"""
### 📊 {yr} – Monthly Demand Pattern

- 🔼 Peak Month: **{peak['Month_Name']}** (₹{peak['Sales']:,.0f})
- 🔽 Slow Month: **{slow['Month_Name']}** (₹{slow['Sales']:,.0f})

Demand pattern indicates **project-driven procurement** in {yr}.
""")




