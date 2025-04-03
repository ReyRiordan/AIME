import pandas as pd
import json
import math

# Load the Excel file
xls = pd.ExcelFile("assignments_original.xlsx")

# Convert each sheet to a dict
sheets_dict = {sheet: xls.parse(sheet).to_dict(orient="records") for sheet in xls.sheet_names}
M1_original = sheets_dict["M1's Randomized Cases"]
M2_original = sheets_dict["M2's Randomized Cases"]

# Methods for cleaning
def valid_student(student, required_keys):
    return all(key in student and not (isinstance(student[key], float) and math.isnan(student[key])) for key in required_keys)

def prepare(original, required_keys):
    cleaned = []
    for student in original:
        if valid_student(student, required_keys):
            cleaned.append({"Last_name": student["LAST_NAME"], 
                    "First_name": student["FIRST_NAME"], 
                    "NetID": student["NetID"], 
                    "First_case": student[required_keys[3]], 
                    "Second_case": student[required_keys[4]]})
            
    formatted = {}
    for student in cleaned:
        noID = {k: v for k, v in student.items() if k != "NetID"}
        formatted[student["NetID"]] = noID
    
    return formatted

# Clean
required_M1 = ["LAST_NAME", "FIRST_NAME", "NetID", "First Case (Atypical 1 - Jenny or Jeffrey)", "Second Case (Atypical 2 - Sam or Sarah)"]
M1 = prepare(M1_original, required_M1)
required_M2 = ["LAST_NAME", "FIRST_NAME", "NetID", "First Case (Atypica 1l)", "Second Case (Atypical 2)"]
M2 = prepare(M2_original, required_M2)

print(dict(list(M2.items())[:5]))

# Check number of students
print(len(M1))
print(len(M2))

# Save to JSONs
# with open("M1_original.json", "w") as json_file:
#     json.dump(M1_original, json_file, indent=2)
# with open("M2_original.json", "w") as json_file:
#     json.dump(M2_original, json_file, indent=2)

# with open("M1.json", "w") as json_file:
#     json.dump(M1, json_file, indent=2)
# with open("M2.json", "w") as json_file:
#     json.dump(M2, json_file, indent=2)

# Exit
print("Conversion complete!")
