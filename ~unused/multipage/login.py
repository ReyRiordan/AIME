import streamlit as st

# st.set_page_config(layout="wide")

# Initialize st.session_state.role to None
if "role" not in st.session_state:
    st.session_state.role = None

# Selectbox to choose role
st.session_state.role = st.selectbox("Select your role:", [None, "student", "teacher", "admin"])

# Redirect to dashboard once logged in
if "role" in st.session_state and st.session_state.role is not None:
    st.switch_page("pages/dashboard.py")