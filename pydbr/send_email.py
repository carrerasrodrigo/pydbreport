# -*- coding: utf-8 -*-
#--------------------------------------
import os, smtplib
try:
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase
    from email.MIMEText import MIMEText
    from email.Utils import formatdate
    from email import Encoders as encoders
    py3 = False
except ImportError:
    # Python 3
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email.utils import formatdate
    from email import encoders
    py3 = True

def send_email(sfrom, to, subject, body, cc=[], bcc=[], files=[], host="localhost",
    port=25, user=None, password=None):
    """Send an email

    :param sfrom: The email of the sender
    :param to: A list of receivers of the email
    :param subject: The subject of the email
    :param body: The body of the email
    :param files: A list of absolute path of the files that we want to attach
        to the email.
    :param host: The host that we want to connect to send the emails
    :param port: The port of the host that we want to connect
    :param user: The user that we want to use in case that authentication
        it's needed
    :param password: The password that we want to use in case that
        authentication it's needed
    """
    msg = MIMEMultipart()
    msg['From'] = sfrom
    msg['To'] = ",".join(to)
    msg['Cc'] = ",".join(cc)
    msg['Bcc'] = ",".join(bcc)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    if py3:
        msg.attach(MIMEText(body, "html"))
    else:
        msg.attach(MIMEText(body, "html", "utf-8"))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        with open(f, "rb") as fr:
            part.set_payload(fr.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    try:
        smtp = smtplib.SMTP(host, port)
        if user is not None:
            smtp.login(user, password)
        smtp.sendmail(sfrom, to + cc + bcc, msg.as_string())
        smtp.close()
    except:
        raise
