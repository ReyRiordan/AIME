import streamlit as st

# Redirect
# if "role" not in st.session_state or st.session_state.role is None:
#     st.switch_page("login.py")

# Stages
INIT = 0
CASE = 1
GRADING_DATA = 2
LABEL_DESCS = 3
GRADING_DIAG = 4

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
        },
        "Grading": {
            "Data Acquisition": {
                "General": {
                    "Introduction": 0,
                    "Confirm Identity": 0,
                    "Establish Chief Concern": 0,
                    "Additional Information": 0,
                    "Medical History": 0,
                    "Surgery Hospitalization": 0,
                    "Medication": 0,
                    "Allergies": 0,
                    "Family History": 0,
                    "Alcohol": 0,
                    "Smoking": 0,
                    "Drug Use": 0,
                    "Employment": 0,
                    "Social Support": 0
                },
                "Dimensions": {
                    "Onset": 0,
                    "Quality": 0,
                    "Location": 0,
                    "Timing": 0,
                    "Pattern": 0,
                    "Exacerbating": 0,
                    "Relieving": 0,
                    "Prior History": 0,
                    "Radiation": 0,
                    "Severity": 0
                },
                "Associated": {},
                "Risk": {}
            },
            "Diagnosis": {
                "Summary": {},
                "Potential": {},
                "Rationale": {},
                "Final": {}
            }
        },
        "Labels": {}
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
            st.rerun()


if st.session_state["stage"] == GRADING_DATA:
    st.title("Grading: Data Acquisition")

    layout1 = st.columns([1, 1])
    with layout1[0]:
        layout11 = st.columns([1, 1])

        layout11[0].subheader("General")
        st.session_state["data_general"] = []
        for label, score in st.session_state["file"]["Grading"]["Data Acquisition"]["General"].items():
            st.session_state["data_general"].append({"label": label, "score": score})
        st.session_state["data_general"] = layout11[0].data_editor(
            data = st.session_state["data_general"],
            width = 1000,
            height = 528,
            column_config = {
                "label": st.column_config.Column(
                    label = "Label",
                    width = "medium",
                    disabled = True
                ),
                "score": st.column_config.NumberColumn(
                    label = "Score",
                    width = "small",
                    min_value = 0,
                    step = 1
                )
            }
        )
        for element in st.session_state["data_general"]:
            st.session_state["file"]["Grading"]["Data Acquisition"]["General"][element["label"]] = element["score"]

        layout11[1].subheader("Dimensions")
        st.session_state["data_dimensions"] = []
        for label, score in st.session_state["file"]["Grading"]["Data Acquisition"]["Dimensions"].items():
            st.session_state["data_dimensions"].append({"label": label, "score": score})
        st.session_state["data_dimensions"] = layout11[1].data_editor(
            data = st.session_state["data_dimensions"],
            width = 1000,
            column_config = {
                "label": st.column_config.Column(
                    label = "Label",
                    width = "medium",
                    disabled = True
                ),
                "score": st.column_config.NumberColumn(
                    label = "Score",
                    width = "small",
                    min_value = 0,
                    step = 1
                )
            }
        )
        for element in st.session_state["data_dimensions"]:
            st.session_state["file"]["Grading"]["Data Acquisition"]["Dimensions"][element["label"]] = element["score"]


        layout12 = st.columns([1, 1])
        layout12[0].subheader("Associated Symptoms")
        st.session_state["data_associated"] = [{"label": None, "score": None}]
        st.session_state["data_associated"] = layout12[0].data_editor(
            data = st.session_state["data_associated"],
            width = 1000,
            num_rows = "dynamic",
            hide_index = True,
            key = "Associated",
            column_config = {
                "label": st.column_config.Column(
                    label = "Label",
                    width = "medium",
                    required = True
                ),
                "score": st.column_config.NumberColumn(
                    label = "Score",
                    width = "small",
                    min_value = 0,
                    step = 1,
                    required = True
                )
            }
        )
        for element in st.session_state["data_associated"]:
            if element["label"] and element["score"]:
                st.session_state["file"]["Grading"]["Data Acquisition"]["Associated"][element["label"]] = element["score"]

        layout12[1].subheader("Risk Factors")
        st.session_state["data_risk"] = [{"label": None, "score": None}]
        st.session_state["data_risk"] = layout12[1].data_editor(
            data = st.session_state["data_risk"],
            width = 1000,
            num_rows = "dynamic",
            hide_index = True,
            key = "Risk",
            column_config = {
                "label": st.column_config.Column(
                    label = "Label",
                    width = "medium",
                    required = True
                ),
                "score": st.column_config.NumberColumn(
                    label = "Score",
                    width = "small",
                    min_value = 0,
                    step = 1,
                    required = True
                )
            }
        )
        for element in st.session_state["data_risk"]:
            if element["label"] and element["score"]:
                st.session_state["file"]["Grading"]["Data Acquisition"]["Risk"][element["label"]] = element["score"]

    with layout1[1]:
        st.subheader("Case Description")
        st.write("INSERT PRETTY PRINT OF CASE DESCRIPTION HERE")

    if st.button("Next"):
        print(st.session_state["file"])
        print("\n\n")
        set_stage(LABEL_DESCS)
        st.rerun()


if st.session_state["stage"] == LABEL_DESCS:
    layout1 = st.columns([1, 3, 1])
    with layout1[1]:
        st.title("Label Descriptions")

        label_list = []
        for label in st.session_state["file"]["Grading"]["Data Acquisition"]["Associated"]:
            label_list.append(label)
        for label in st.session_state["file"]["Grading"]["Data Acquisition"]["Risk"]:
            label_list.append(label)

        for label in label_list:
            st.session_state["file"]["Labels"][label] = st.text_input(label)
        
        if st.button("Next"):
            print(st.session_state["file"])
            print("\n\n")
            set_stage(GRADING_DIAG)
            st.rerun()