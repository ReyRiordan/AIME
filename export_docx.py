import aspose.words as aw
from datetime import date

def exportAsDocx(PROMPT: str, MODEL: str, messageList: list[str]):
    # Initialization
    today = date.today()
    date_text = today.strftime("%b-%d-%Y")
    doc = aw.Document()
    builder = aw.DocumentBuilder(doc)
    
    # Header
    font = builder.font
    font.size = 14
    font.bold = True
    font.name = "Arial"
    builder.writeln("Date: " + date_text + " Model: " + MODEL + " Prompt: " + PROMPT)
    builder.writeln()

    # Convo
    font.size = 12
    font.bold = False
    count = 0
    for msg in messageList:
        if count%2 == 0: builder.writeln("User: " + msg)
        else: builder.writeln("GPT: " + msg)
        count += 1

    # Save
    doc.save("Convo_" + date_text + ".docx")