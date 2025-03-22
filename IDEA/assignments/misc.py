import pandas as pd
import json
import math

# Load the Excel file with all sheets
xls = pd.ExcelFile("assignments_original.xlsx")

# Convert each sheet to a dictionary of lists
sheets_dict = {sheet: xls.parse(sheet).to_dict(orient="records") for sheet in xls.sheet_names}
M1_original = sheets_dict["M1's Randomized Cases"]

M1 = []
required_keys = ["LAST_NAME", "FIRST_NAME", "NetID", "First Case (Atypical 1 - Jenny or Jeffrey)", "Second Case (Atypical 2 - Sam or Sarah)"]
for student in M1_original:
    if all(key in student and not (isinstance(student[key], float) and math.isnan(student[key])) for key in required_keys):
        M1.append({"Last_name": student["LAST_NAME"], 
                   "First_name": student["FIRST_NAME"], 
                   "NetID": student["NetID"], 
                   "First_case": student["First Case (Atypical 1 - Jenny or Jeffrey)"], 
                   "Second_case": student["Second Case (Atypical 2 - Sam or Sarah)"]})


# Save to a properly formatted JSON file
with open("M1_original.json", "w") as json_file:
    json.dump(M1_original, json_file, indent=2)

with open("M1.json", "w") as json_file:
    json.dump(M1, json_file, indent=2)

print("Conversion complete!")
