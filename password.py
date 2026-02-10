import streamlit as st

# -----------------------------
# CHANGE THESE CREDENTIALS
# -----------------------------
ALLOWED_USER = "KARTHIK"
ALLOWED_PASS = "KARTHIK@2026"

def login_required():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title(" Secure Login")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            if user == ALLOWED_USER and pwd == ALLOWED_PASS:
                st.session_state.logged_in = True
                st.success("Login successful ✅")
                st.rerun()
            else:
                st.error("Invalid username or password ❌")

        st.stop()

