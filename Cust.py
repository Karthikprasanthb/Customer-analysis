# =====================================================
# STREAMLIT: RING & MATERIAL DEEP PORTFOLIO ANALYSIS
# =====================================================

import streamlit as st
from password import login_required
login_required() 
import pandas as pd
import plotly.express as px 
from filter import sidebar_filters

def show_values(fig):
    fig.update_traces(
        texttemplate="%{y:,.0f}",
        textposition="outside",
        textfont=dict(
            color="#1f1f1f",   # ✅ DARK VALUE LABELS
            size=12
        )
    )

    fig.update_layout(
        # ✅ DARK AXIS LABELS (VALID PROPERTIES ONLY)
        xaxis=dict(
            tickfont=dict(color="#1f1f1f", size=11)
        ),
        yaxis=dict(
            tickfont=dict(color="#1f1f1f", size=11)
        ),

        # ✅ DARK TITLE (CORRECT WAY)
        title=dict(
            font=dict(color="#1f1f1f", size=16)
        ),

        uniformtext_minsize=12,
        uniformtext_mode="hide"
    )

    return fig



st.set_page_config(page_title="Ring & Material Deep Analysis", layout="wide")

# =====================================================
# CONFIG
# =====================================================
import os

# =====================================================
# CONFIG
# ====================================================DATA_FILE = "Sales_Data3.xlsx"
DATA_FILE = "DATA .xlsx"


TARGET_CUSTOMERS = [
   "ABCD SOLUTION",
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
# DERIVED COLUMNS (MUST BE BEFORE FILTERS)
# =====================================================
df["Month"] = df["Cleaned PO Date"].dt.strftime("%b")

# =====================================================
# GLOBAL FILTERS (SHARED ACROSS ALL PAGES)
# =====================================================
customers, start_date, end_date, months = sidebar_filters(df)

filtered = df[
    (df["Customer"].isin(customers)) &
    (df["Cleaned PO Date"].dt.date >= start_date) &
    (df["Cleaned PO Date"].dt.date <= end_date) &
    (df["Month"].isin(months))
]

if filtered.empty:
    st.warning("⚠️ No data found for the selected date range.")
    st.stop()

# =====================================================
# DERIVED COLUMNS
# =====================================================
# =====================================================
# DERIVED COLUMNS (AFTER FILTERING)
# =====================================================
filtered["Year"] = filtered["Cleaned PO Date"].dt.year
filtered["Month"] = filtered["Cleaned PO Date"].dt.strftime("%b")
filtered["Month_Period"] = (
    filtered["Cleaned PO Date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

# =====================================================
# HEADER
# =====================================================
st.title(" Ring & Material – Deep  Analysis")
# st.caption(f"Selected Customers: {', '.join(customers)}")

# =====================================================
# KPI SUMMARY
# =====================================================
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Sales (INR)", f"₹{filtered['Product value INR'].sum():,.0f}")
c2.metric("Total Qty", f"{filtered['Qty'].sum():,.0f}")
c3.metric("Total Orders", filtered.shape[0])
c4.metric("Avg Order Value", f"₹{filtered['Product value INR'].mean():,.0f}")
c5.metric("Avg Order Qty", f"{filtered['Qty'].mean():,.0f}")

# =====================================================
# DEEP THEORY ANALYSIS
# =====================================================
st.markdown("#  Analysis Summary")

if not filtered.empty:
    ring_agg = (
       filtered.groupby("Ring", dropna=False)
       .agg(
           Sales=("Product value INR","sum"),
           Qty=("Qty","sum")
        )
        .reset_index()
    )

    material_agg = filtered.groupby("Material").agg(
        Sales=("Product value INR","sum"),
        Qty=("Qty","sum")
    )
    rm_agg = filtered.groupby(["Ring","Material"]).agg(
        Sales=("Product value INR","sum"),
        Qty=("Qty","sum")
    )

    top_ring = ring_agg.sort_values("Sales", ascending=False).index[0]
    top_material = material_agg.sort_values("Sales", ascending=False).index[0]
    top_rm = rm_agg.sort_values("Sales", ascending=False).index[0]
    # -----------------------------
# MONTHLY BEHAVIOR ANALYSIS
# -----------------------------
    monthly_summary = (
        filtered.groupby("Month_Period")
        .agg(
             Sales=("Product value INR", "sum"),
             Qty=("Qty", "sum"),
             Orders=("Qty", "count")
            )
        .reset_index()
)

# Convert month to readable label
    monthly_summary["Month_Label"] = monthly_summary["Month_Period"].dt.strftime("%b %Y")

# Peak month (highest sales)
    # Peak month (highest sales)
    peak_row = monthly_summary.sort_values("Sales", ascending=False).iloc[0]

# Slow month (lowest sales but > 0)
    non_zero = monthly_summary[monthly_summary["Sales"] > 0]
    slow_row = non_zero.sort_values("Sales", ascending=True).iloc[0] if not non_zero.empty else None

# Check if only one active month
    same_month = False
    if slow_row is not None and peak_row["Month_Label"] == slow_row["Month_Label"]:
        same_month = True

# No order months
    zero_months = monthly_summary[monthly_summary["Orders"] == 0]["Month_Label"].tolist()

    # st.markdown("###  Business Timing & Demand Insight")

# -----------------------------
# OVERALL PERFORMANCE (ALWAYS)
# -----------------------------
    st.write(f"""
    **Overall Performance**
    - The selected customers generated a total sales value of
    **₹{filtered['Product value INR'].sum():,.0f}**
    with a movement of **{filtered['Qty'].sum():,.0f} units**
    during the selected period.
    """)

# -----------------------------
# PEAK / SLOW LOGIC
# -----------------------------

# Case 1: Only one active month
    if same_month:

       st.write(f"""
       **Demand Insight**
       - Only one active buying month (**{peak_row['Month_Label']}**) was observed
       during the selected period, contributing
       **₹{peak_row['Sales']:,.0f}** in sales.
       This indicates **limited activity or a single procurement cycle**.
       """)

# Case 2: Normal scenario
    else:

       st.write(f"""
       **Peak Buying Period**
       - The highest buying activity was observed in
        **{peak_row['Month_Label']}**, contributing
        **₹{peak_row['Sales']:,.0f}** in sales.
        """)

       if slow_row is not None:
           st.write(f"""
           **Slow Activity Period**
           - The slowest sales period was
           **{slow_row['Month_Label']}**
           with only **₹{slow_row['Sales']:,.0f}** in value,
           indicating low operational or procurement activity.
           """)




# =====================================================
# 1️⃣ TOP RING — SEPARATE SALES & QTY
# =====================================================
st.markdown("## 1️ Top Ring")

tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])

with tab_sales:
    fig = px.bar(
        ring_agg.reset_index().sort_values("Sales", ascending=False),
        x="Ring",
        y="Sales",
        title="Top Rings by Sales Value",
        text_auto=True
     )
    fig = show_values(fig)
    st.plotly_chart(fig, use_container_width=True)


with tab_qty:
    fig = px.bar(
        ring_agg.reset_index().sort_values("Qty", ascending=False),
        x="Ring",
        y="Qty",
        title="Top Rings by Quantity",
        text_auto=True
    )
    fig = show_values(fig)
    st.plotly_chart(fig, use_container_width=True)
# 🔍 TOP RING SUMMARY (DETAILED)
year_text = f"{start_date} to {end_date}"
month_text = ", ".join(months)
if not ring_agg.empty:
    top_ring_row = ring_agg.sort_values("Sales", ascending=False).iloc[0]

    st.info(f"""
    **Top Ring Insight ({year_text} | {month_text})**

    - The ring **{top_ring_row['Ring']}** emerged as the highest contributor
    during the selected period, generating **₹{top_ring_row['Sales']:,.0f}**
    in sales with a total movement of **{top_ring_row['Qty']:,.0f} units**.
    - This indicates **strong demand concentration** for this ring across
    the selected months and years.
    """)



# =====================================================
# 2️⃣ TOP MATERIAL — SEPARATE SALES & QTY
# =====================================================
st.markdown("## 2️ Top Material")

tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])

with tab_sales:
    fig = px.bar(
        material_agg.reset_index().sort_values("Sales", ascending=False),
        x="Material",
        y="Sales",
        title="Top Materials by Sales Value",
        text_auto=True
    )
    fig = show_values(fig)
    st.plotly_chart(fig, use_container_width=True)


with tab_qty:
    fig = px.bar(
        material_agg.reset_index().sort_values("Qty", ascending=False),
        x="Material",
        y="Qty",
        title="Top Materials by Quantity",
        text_auto=True
    )
    fig = show_values(fig)
    st.plotly_chart(fig, use_container_width=True)
# 🔍 TOP MATERIAL SUMMARY
# 🔍 TOP MATERIAL SUMMARY (DETAILED)
if not material_agg.empty:
    top_material_row = material_agg.sort_values("Sales", ascending=False).iloc[0]

    st.info(f"""
    **Top Material Insight ({year_text} | {month_text})**

    - The material **{top_material_row.name}** recorded the highest consumption
    value during the selected period, contributing **₹{top_material_row['Sales']:,.0f}**
    with **{top_material_row['Qty']:,.0f} units** supplied.
    - This suggests **material standardization or repeated usage**
    across projects executed in these months.
    """)



# =====================================================
# 3️⃣ RING + MATERIAL — SEPARATE SALES & QTY
# =====================================================
st.markdown("## 3️ Ring + Material")

rm_df = rm_agg.reset_index()
rm_df["Ring_Material"] = rm_df["Ring"] + " | " + rm_df["Material"]

tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])

with tab_sales:
    top_sales = rm_df.sort_values("Sales", ascending=False).head(15)
    fig = px.bar(
        top_sales,
        x="Ring_Material",
        y="Sales",
        title="Top Ring + Material by Sales Value",
        text_auto=True
    )
    fig = show_values(fig)
    st.plotly_chart(fig, use_container_width=True)


with tab_qty:
    top_qty = rm_df.sort_values("Qty", ascending=False).head(15)
    fig = px.bar(
        top_qty,
        x="Ring_Material",
        y="Qty",
        title="Top Ring + Material by Quantity",
        text_auto=True
    )
    fig = show_values(fig)
    st.plotly_chart(fig, use_container_width=True)


st.dataframe(rm_df.sort_values("Sales", ascending=False), use_container_width=True)
# 🔍 RING + MATERIAL SUMMARY
# 🔍 RING + MATERIAL SUMMARY (DETAILED)
if not rm_agg.empty:
    top_rm_row = rm_agg.sort_values("Sales", ascending=False).iloc[0]

    st.info(f"""
    **Top Ring–Material Combination Insight ({year_text} | {month_text})**

    - The combination **{top_rm_row.name[0]} | {top_rm_row.name[1]}**
    delivered the highest business value during the selected period,
    generating **₹{top_rm_row['Sales']:,.0f}** with
    **{top_rm_row['Qty']:,.0f} units** supplied.
    - This combination represents a **critical configuration**
    frequently ordered during these months.
    """)

# =====================================================
# 4️⃣ MONTH-WISE — SEPARATE SALES & QTY
# =====================================================
st.markdown("## 4️ Month-wise Trend")

monthly = filtered.groupby("Month_Period").agg(
    Sales=("Product value INR","sum"),
    Qty=("Qty","sum")
).reset_index()

tab_sales, tab_qty = st.tabs([" Sales Value", " Quantity"])

with tab_sales:
    fig = px.line(
       monthly,
       x="Month_Period",
       y="Sales",
       markers=True,
      title="Month-wise Sales Trend"
     )

    fig.update_traces(
        text=monthly["Sales"],
        textposition="top center"
    )

    st.plotly_chart(fig, use_container_width=True)


with tab_qty:
    fig = px.line(
       monthly,
       x="Month_Period",
       y="Qty",
       markers=True,
       title="Month-wise Quantity Trend"
    )

    fig.update_traces(
        text=monthly["Qty"],
        textposition="top center"
    )

    st.plotly_chart(fig, use_container_width=True)
# 🔍 MONTH-WISE TREND SUMMARY
# 🔍 MONTH-WISE TREND SUMMARY (DETAILED)
if not monthly_summary.empty:
    peak_month_row = monthly_summary.sort_values("Sales", ascending=False).iloc[0]

    st.info(f"""
    **Month-wise Demand Insight ({year_text})**

    - Peak demand was observed in **{peak_month_row['Month_Label']}**
    with total sales of **₹{peak_month_row['Sales']:,.0f}**.
    - The overall trend across selected months (**{month_text}**)
    reflects **project-based and non-uniform procurement behavior**
    rather than consistent monthly ordering.
    """)




