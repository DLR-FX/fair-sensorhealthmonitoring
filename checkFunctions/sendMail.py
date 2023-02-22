import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import checkFunctions.createPDF as cPDF

class MailClient():
    def __init__(self):
        self.port = 587
        self.smtp_server = "smtp.gmail.com"
        self.sender_email = "mvondepkaprondzinski@gmail.com"
        self.receiver_email = "martin.vondepkaprondzinski@dlr.de"
        self.password = "gozveZ-zidtiq-9penmi"
        self.msg = MIMEMultipart()
        self.PDF = cPDF.SetupPDF()

    def set_mail_content(self, warnings):
        self.PDF.setContentPDF(warnings)
        self.msg['Subject'] = "Sensor Monitoring Report"
        self.msg['From'] = self.sender_email
        self.msg['To'] = self.receiver_email
        self.msg.attach(MIMEText("", 'plain'))

        binary_pdf = open("Warnings.pdf", "rb")
        payload = MIMEBase("application", "octate-stream", Name="Warnings.pdf")
        payload.set_payload((binary_pdf).read())
        encoders.encode_base64(payload)
        payload.add_header("Content-Decomposition", "attachment", filename="Warnings.pdf")
        self.msg.attach(payload)

    def sendMail(self):
        context = ssl.create_default_context()
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, self.receiver_email, self.msg.as_string())
