import streamlit as st

# Redirect
if "role" not in st.session_state or st.session_state.role is None:
    st.switch_page("login.py")

st.title("Dashboard")

def new_interview():
    st.switch_page("pages/simulation.py")

def new_patient():
    st.switch_page("pages/creation.py")


# Interviews
if st.session_state.role in ["student", "teacher", "admin"]:
    st.header("Interviews", divider="grey")
    if st.button("NEW INTERVIEW", use_container_width=True, type="primary"):
        new_interview()

# Patients
if st.session_state.role in ["teacher", "admin"]:
    st.header("Patients", divider="grey")
    if st.button("NEW PATIENT", use_container_width=True, type="primary"):
        new_patient()