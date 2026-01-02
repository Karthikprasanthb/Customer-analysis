import streamlit as st
import pandas as pd

def sidebar_filters(df):
    st.sidebar.header("🔎 Global Filters")

    # ---------------- CUSTOMER ----------------
    if "customers" not in st.session_state:
        st.session_state.customers = sorted(df["Customer"].unique())

    customers = st.sidebar.multiselect(
        "Select Customer(s)",
        options=sorted(df["Customer"].unique()),
        default=st.session_state.customers,
        key="customers"
    )
    
    
    # ---------------- DATE RANGE ----------------
    df_dates = df["Cleaned PO Date"].dropna()

    min_date = df_dates.min().date()
    max_date = df_dates.max().date()

    # Ensure session state always stores a tuple
    if "date_range" not in st.session_state or not isinstance(st.session_state.date_range, tuple):
        st.session_state.date_range = (min_date, max_date)

    st.sidebar.subheader("📅 Date Filter")

# Initialize defaults
    if "start_date" not in st.session_state:
        st.session_state.start_date = min_date

    if "end_date" not in st.session_state:
        st.session_state.end_date = max_date

# FROM DATE
    start_date = st.sidebar.date_input(
        "From Date",
        value=st.session_state.start_date,
        min_value=min_date,
        max_value=max_date,
        key="start_date"
    )

# TO DATE
    end_date = st.sidebar.date_input(
       "To Date",
        value=st.session_state.end_date,
        min_value=min_date,
        max_value=max_date,
        key="end_date"
    )

# Safety check (user selects wrong order)
    if start_date > end_date:
       st.sidebar.error("⚠️ From Date cannot be after To Date")
       st.stop()

    # ---------------- MONTH ----------------
    month_list = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

    if "months" not in st.session_state:
        st.session_state.months = month_list

    months = st.sidebar.multiselect(
        "Select Month(s)",
        options=month_list,
        default=st.session_state.months,
        key="months"
    )

    return customers, start_date, end_date, months
