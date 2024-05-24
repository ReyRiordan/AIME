import streamlit as st

# Redirect
if "role" not in st.session_state or st.session_state.role is None:
    st.switch_page("login.py")