# -*- coding: utf-8 -*-

import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

logger = logging.getLogger("pydbr")


def send_email(
    sfrom,
    to,
    subject,
    body,
    cc=[],
    bcc=[],
    files=[],
    links=[],
    host="localhost",
    port=25,
    user=None,
    password=None,
):
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
    logger.info("building email {}".format(subject))

    msg = MIMEMultipart()
    msg["From"] = sfrom
    msg["To"] = ",".join(to)
    msg["Cc"] = ",".join(cc)
    msg["Bcc"] = ",".join(bcc)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    if len(links) > 0:
        body += "<br><br>"
        for link_data in links:
            body += f'<a href="{link_data["link"]}">{link_data["name"]}</a><br>'

    msg.attach(MIMEText(body, "html"))

    for f in files:
        part = MIMEBase("application", "octet-stream")
        with open(f, "rb") as fr:
            part.set_payload(fr.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            'attachment; filename="%s"' % os.path.basename(f),
        )
        msg.attach(part)

    try:
        smtp = smtplib.SMTP(host, port)
        if user is not None:
            smtp.login(user, password)
        smtp.sendmail(sfrom, to + cc + bcc, msg.as_string())
        smtp.close()
        logger.info("email sent {}".format(subject))
    except Exception:
        raise
