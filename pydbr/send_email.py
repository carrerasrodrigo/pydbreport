#--------------------------------------
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email import Encoders
import smtplib, os

def send_email(sfrom, to, subject, body, files=[], host="localhost",
    port=25):
    msg = MIMEMultipart()
    msg['From'] = sfrom
    msg['To'] = ",".join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, "html"))
    
    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f,"rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)
    
    try:
        smtp = smtplib.SMTP(smtp_host, smtp_port)
        smtp.sendmail(sfrom, to, msg.as_string())
        smtp.close()
    except:
        print("Error sending the email")