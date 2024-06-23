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
        "Speech": {
            "Host": "openai",
            "Model": "tts-1",
            "Voice": None
        },
        "Assets": None,
        "Case": {
            "Personal Details": {},
            "Chief Concern": None,
            "HIPI": {
                "Onset": {"desc": None, "lock": None},
                "Quality": {"desc": None, "lock": None},
                "Location": {"desc": None, "lock": None},
                "Timing": {"desc": None, "lock": None},
                "Pattern": {"desc": None, "lock": None},
                "Severity": {"desc": None, "lock": None},
                "Prior History": {"desc": None, "lock": None},
                "Radiation": {"desc": None, "lock": None},
                "Exacerbating Factors": {"desc": None, "lock": None},
                "Relieving Factors": {"desc": None, "lock": None}
            },
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


# Init
if st.session_state["stage"] == INIT:
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("The Basics")

        st.session_state["file"]["ID"] = st.text_input("Enter the unique ID for your patient:")

        st.session_state["file"]["Speech"]["Voice"] = st.selectbox("Choose your patient's voice:", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

        if st.button("Next"):
            # st.session_state["file"]["ID"] = id
            # st.session_state["file"]["Speech"]["Voice"] = voice
            print(st.session_state["file"])
            print("\n\n")
            set_stage(CASE)
            st.rerun()


# Case
if st.session_state["stage"] == CASE:
    layout1 = st.columns([1, 3, 1])
    with layout1[1]:
        st.title("Case Description")

        st.subheader("Personal Details")
        st.session_state["file"]["Case"]["Personal Details"]["Name"] = st.text_input("Enter patient's full name:")
        st.session_state["file"]["Case"]["Personal Details"]["Sex"] = st.text_input("Enter patient's sex:")
        st.session_state["file"]["Case"]["Personal Details"]["Race"] = st.text_input("Enter the patient's race:")
        st.session_state["file"]["Case"]["Personal Details"]["Birthdate"] = st.text_input("Enter patient's birthdate:")
        st.session_state["file"]["Case"]["Personal Details"]["Tone"] = st.text_input("Enter patient's tone during interview:")
        
        st.subheader("Chief Concern")
        chief_concern = st.text_input("Enter patient's chief concern in second person perspective:")

        st.subheader("History of Present Illness")
        for dim in st.session_state["file"]["Case"]["HIPI"]:
            layout11 = st.columns([7, 1])
            st.session_state["file"]["Case"]["HIPI"][dim]["desc"] = layout11[0].text_input(dim + ":")
            layout11[1].markdown("#")
            st.session_state["file"]["Case"]["HIPI"][dim]["lock"] = layout11[1].toggle(label="lock", key=dim)

        st.subheader("Associated Symptoms")
        id = 1
        n = 1
        for element in st.session_state["file"]["Case"]["Associated Symptoms"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Associated Symptoms"):
            st.session_state["file"]["Case"]["Associated Symptoms"].append({"desc": None, "lock": False})
            st.rerun()

        st.subheader("Medical History")
        n = 1
        for element in st.session_state["file"]["Case"]["Medical History"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Medical History"):
            st.session_state["file"]["Case"]["Medical History"].append({"desc": None, "lock": False})
            st.rerun()

        st.subheader("Surgical History")
        n = 1
        for element in st.session_state["file"]["Case"]["Surgical History"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Surgical History"):
            st.session_state["file"]["Case"]["Surgical History"].append({"desc": None, "lock": False})
            st.rerun()

        st.subheader("Medications")
        n = 1
        for element in st.session_state["file"]["Case"]["Medications"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Medications"):
            st.session_state["file"]["Case"]["Medications"].append({"desc": None, "lock": False})
            st.rerun()

        st.subheader("Allergies")
        n = 1
        for element in st.session_state["file"]["Case"]["Allergies"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Allergies"):
            st.session_state["file"]["Case"]["Allergies"].append({"desc": None, "lock": False})
            st.rerun()

        st.subheader("Family History")
        n = 1
        for element in st.session_state["file"]["Case"]["Family History"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Family History"):
            st.session_state["file"]["Case"]["Family History"].append({"desc": None, "lock": False})
            st.rerun()

        st.subheader("Social History")
        n = 1
        for element in st.session_state["file"]["Case"]["Social History"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Social History"):
            st.session_state["file"]["Case"]["Social History"].append({"desc": None, "lock": False})
            st.rerun()
        
        st.subheader("Other Symptoms")
        n = 1
        for element in st.session_state["file"]["Case"]["Other Symptoms"]:
            layout12 = st.columns([7, 1])
            element["desc"] = layout12[0].text_input("Element " + str(n), key=id)
            layout12[1].markdown("#")
            element["lock"] = layout12[1].toggle(label="lock", key=id+999)
            n += 1
            id += 1
        if st.button("Add New Element", type="primary", key="Other Symptoms"):
            st.session_state["file"]["Case"]["Other Symptoms"].append({"desc": None, "lock": False})
            st.rerun()

        if st.button("Next"):
            print(st.session_state["file"])
            print("\n\n")
            set_stage(GRADING_DATA)