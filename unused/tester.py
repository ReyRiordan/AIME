from docx import Document
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
import os
import datetime as date
import base64
import io
import website_methods as methods
from webapp.lookups import *



"""
messages = [{"role" : "Monke", "content" : "oo oo aa aa"}]
interview = methods.create_interview_file("Me", "Ooof", messages)
interview.save("./testing/monkeee.docx")
"""

"""
interview = Document()
interview.add_paragraph("OO OO AA AA SCREEEEEEÊEĒEECH")
currentDateAndTime = date.datetime.now()
date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
bio = io.BytesIO()
interview.save(bio)
methods.send_email(bio, EMAIL_TO_SEND, "Osama", date_time, "tf goin on")
"""