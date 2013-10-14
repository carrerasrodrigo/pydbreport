#--------------------------------------
import os, smtplib
try:
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase
    from email.MIMEText import MIMEText
    from email.Utils import formatdate    
    from email import Encoders as encoders
except ImportError:
    # Python 3
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email.utils import formatdate
    from email import encoders

def send_email(sfrom, to, subject, body, files=[], host="localhost",
    port=25):
    """Send an email

    :param sfrom: The email of the sender
    :param to: A list of receivers of the email
    :param subject: The subject of the email
    :param body: The body of the email
    :param files: A list of absolute path of the files that we want to attach
        to the email.
    :param host: The host that we want to connect to send the emails
    :param port: The port of the host that we want to connect
    :returns: A list of ElementTree
    """
    msg = MIMEMultipart()
    msg['From'] = sfrom
    msg['To'] = ",".join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, "html"))
    
    for f in files:
        part = MIMEBase('application', "octet-stream")
        with open(f, "rb") as fr:
            part.set_payload(fr.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)
    
    try:
        smtp = smtplib.SMTP(host, port)
        smtp.sendmail(sfrom, to, msg.as_string())
        smtp.close()
    except:
        print("Error sending the email")
