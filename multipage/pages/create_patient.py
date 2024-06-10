import streamlit as st

# Redirect
# if "role" not in st.session_state or st.session_state.role is None:
#     st.switch_page("login.py")

# Stages
INIT = 0
CASE = 1
GRADING_DATA = 2
GRADING_DIAG = 3

st.set_page_config(page_title = "Creation", layout = "wide")

if "file" not in st.session_state:
    st.session_state["file"] = {
        "ID": None,
        "Speech": {},
        # FILE UPLOADS?
        "Case": {
            "Personal Details": [],
            "Chief Concern": None,
            "HIPI": [],
            "Associated Symptoms": [],
            "Medical History": [],
            "Surgical History": [],
            "Medications": [],
            "Allergies": [],
            "Family History": [],
            "Social History": [],
            "Other Symptoms": []
        }
    }

if "stage" not in st.session_state:
    st.session_state["stage"] = INIT

def set_stage(stage):
    st.session_state["stage"] = stage


# Initialization
if st.session_state["stage"] == INIT:
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("The Basics")
        id = st.text_input("Enter the unique ID for your patient:")
        voice = st.selectbox("Choose your patient's voice:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
        if st.button("Next"):
            st.session_state["file"]["ID"] = id
            st.session_state["file"]["Speech"] = {
                "host": "openai",
                "model": "tts-1",
                "voice": voice
            }
            set_stage(CASE)
