# -*- coding: utf-8 -*-
#!/usr/bin/python
import argparse
import csv
import datetime
import logging
import os
import sys

from .schedulerconf import start_loop
from .send_email import send_email
from jinja2 import Template
from sqlalchemy import create_engine
import sqlalchemy
from xml.etree import ElementTree as ET


logger = logging.getLogger('pydbr')


def read_query(p):
    with open(p, "r") as f:
        return ET.XML(f.read())


def scan_queries(path):
    """Scans all xml files based on the extension

    :param path: The folder path that it's gonna be scanned
    :returns: A list of ElementTree
    """
    ret = []
    for root, dirs, files in os.walk(path):
        for f in filter(lambda x: x.endswith(".xml"), files):
            p = os.path.join(root, f)
            ret.append(read_query(p))
    return ret


def get_connection_query(db_type, db_name, user, password, host, db_options):
    if db_type == 'sqlite':
        return u'sqlite:///{db_name}?{db_options}'.format(db_name=db_name,
            db_options=db_options)
    else:
        return u'{db_type}://{db_user}:{db_password}@{host}/{db_name}' \
            '?{db_options}'.format(
                db_type=db_type, db_name=db_name, db_user=user,
                db_password=password, host=host, db_options=db_options)


def run_query(db_type, db_name, user, password, host, db_options, query):
    """Run a SQL query

    :param db_type: The type of connection available
    :param db_name: The name of the database
    :param user: The connection user for the database
    :param password: The password to connect to the database
    :param host: The host where you are going to connect
    :param db_options: The options to configure the db
    :param query: The query that you want to run
    :returns: A matrix of queries
    """
    password = u"" if password is None else password
    db_options = u"" if db_options is None else db_options

    conn_query = get_connection_query(db_type, db_name, user, password, host,
        db_options)
    engine = create_engine(conn_query)
    conn = engine.connect()
    result = conn.execute(query)

    rows = []
    try:
        if len(result.keys()) > 0:
            rows = [result.keys()] + result.fetchall()
    except sqlalchemy.exc.ResourceClosedError:
        pass
    conn.close()
    return rows


def render_table(query, table):
    """Renders a matrix into a html table

    :param query: The query that you are rendering
    :param matrix: The matrix that you want to render
    :returns: An string representing an html table
    """
    if query.find("template_path") is None:
        template_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "templates", "base.jinja")
    else:
        template_path = query.find("template_path").text
    transpose = query.find("transpose").text == "1"

    try:
        title = query.find("title").text
    except AttributeError:
        title = None

    with open(template_path, "r") as f:
        template_content = f.read()

    template = Template(template_content)
    return template.render(table=table, transpose=transpose, title=title)


def generate_csv(name, table):
    """Generates a csv file based on a matrix

    :param name: The full path of the csv file, for example file.csv
    :param table: The matrix that we want to add into the csv
    :returns: The full path of the csv
    """
    with open(name, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in table:
            writer.writerow(row)
    return name


def parse_var(val):
    if val is not None and val.startswith('$ENV:'):
        return os.environ.get(val.replace('$ENV:', ''))
    return val


def __hour_is_ok(xml):
    if xml.find("cron") is not None:
        return True

    hour = datetime.datetime.now().hour
    hours = xml.find("hours")
    if hours is not None:
        l = hours.text.replace(" ", "").split(",")
        return str(hour) in l or "*" in l
    return True


def __day_is_ok(xml):
    if xml.find("cron") is not None:
        return True

    day = datetime.datetime.now().day
    weekday = datetime.datetime.now().weekday()
    days = xml.find("day")
    weekdays = xml.find("weekday")

    if days is not None:
        l = days.text.replace(" ", "").split(",")
        return (str(day) in l or "*" in l) and __hour_is_ok(xml)

    if weekdays is not None:
        l = weekdays.text.replace(" ", "").split(",")
        return (str(weekday) in l or "*" in l) and __hour_is_ok(xml)

    return False


def print_email_on_screen(body, csv_files):
    """Prints information in the standar output

    :param body: An string representing the body of an email
    :param csv_files: a list of csv paths
    """
    print("Body:")
    print(body)
    print("CSV Files:")
    for cv in csv_files:
        print(cv)


def __find_variables(queries):
    data = [(q.find("variable").text, "")
        for q in queries if q.find("variable") is not None]
    return dict(data)


def __replace_query_variables(query, variables):
    for k, v in variables.items():
        query = query.replace(k, v)
    return query


def process_xml(conf, xml):
    el = []
    csvs = []
    if not __day_is_ok(xml):
        # Ignores the xml files that we dont have to run that day
        return
    variables = __find_variables(xml.find("./queries"))
    send_empty_email = xml.find("send_empty_email")
    for query in xml.find("./queries"):
        sql = __replace_query_variables(query.find("code").text, variables)

        try:
            table = run_query(
                parse_var(query.find("db_type").text),
                parse_var(query.find("db_name").text),
                parse_var(query.find("db_user").text),
                parse_var(query.find("db_password").text),
                parse_var(query.find("db_host").text),
                parse_var(query.find("db_options").text),
                sql
            )
        except Exception:
            logger.error('Error running query: %s', sql)
            raise

        if len(table) <= 1 and send_empty_email is not None \
                and send_empty_email.text == "0":
            continue

        if query.find("transpose").text != "0":
            table = zip(*table)

        if query.find("variable") is not None:
            variables[query.find("variable").text] = str(table[1][0])
        elif query.find("csv").text != "0":
            cs_name = os.path.join(conf.tmp_folder,
                query.find("csv_name").text)
            cs = generate_csv(cs_name, table)
            csvs.append(cs)
        else:
            el.extend(render_table(query, table))

    logger.info(u'done executing queries {}'.format(xml.find('subject').text))

    emails = []
    if conf.output == "email":
        cc = []
        bcc = []
        if conf.emails is not None:
            emails = conf.emails.split("|")
        else:
            for em in xml.findall("*/email"):
                emails.append(em.text)

            for em in xml.findall("*/cc"):
                cc.append(em.text)

            for em in xml.findall("*/bcc"):
                bcc.append(em.text)

        if len(emails) > 0 and (len(el) > 0 or len(csvs) > 0):
            send_email(xml.find("sender").text, emails,
                xml.find("subject").text,
                "".join(el), cc=cc, bcc=bcc, files=csvs,
                host=conf.smtp_host, port=conf.smtp_port,
                user=conf.smtp_user, password=conf.smtp_password)
    else:
        print_email_on_screen("".join(el), csvs)


def configure_logging(log_folder, log_level):
    p = os.path.join(log_folder, 'pydbr.log')
    fh = logging.FileHandler(p)
    formatter = logging.Formatter('%(asctime)s - %(name)s - '
        '%(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(log_level)


parser = argparse.ArgumentParser(description="PyDbReport", add_help=True)
parser.add_argument("--output", help="email or screen. If it's email it will send the report by email otherwise will print it on the screen", default="email")
parser.add_argument("--emails", help="Ignores the list of emails added in the xml file and send to the indicated emails. Ex: ema1@compar.com|em@asd.com", default=None, required=False)
parser.add_argument("--xml", help="The path of the xml that you want to use. If it's not used the script will read all the *.xml from the works folder", default=None, required=False)
parser.add_argument("--reportpath", help="The path where we want to scan all our reports. It's ignored if the --xml argument it's present. ", default=None)
parser.add_argument("--smtp-host", help="The SMTP host", default="localhost", dest="smtp_host")
parser.add_argument("--smtp-port", help="The SMTP host port", default="25", dest="smtp_port")
parser.add_argument("--smtp-user", help="The SMTP user. If Login it's required", default=None, dest="smtp_user")
parser.add_argument("--smtp-password", help="The SMTP password. If Login it's required", default=None, dest="smtp_password")
parser.add_argument("--csv-tmp-folder", help="The folder where the csv files will be saved temporarily", default="/tmp", dest="tmp_folder")
parser.add_argument("--log-folder", help="The folder where the query errors will be logged", default=None, dest="log_folder")
parser.add_argument("--beat", help="Tell's pydbr to engage beat mode", action="store_true", dest="beat")
parser.add_argument("--log-level", help="Indicates the log level", dest="log_level", default=logging.DEBUG)


def main(*args):
    conf = parser.parse_args(args) if len(args) > 0 else parser.parse_args()

    if conf.xml is None and conf.reportpath is None:
        raise Exception("Please use --xml or --reportpath")

    if conf.log_folder is not None:
        configure_logging(conf.log_folder, conf.log_level)

    if conf.xml is None:
        xmls = scan_queries(conf.reportpath)
    else:
        xmls = [read_query(conf.xml)]

    if conf.beat:
        start_loop(conf, process_xml, xmls)
    else:
        for xml in xmls:
            process_xml(conf, xml)

    return True


if __name__ == '__main__':
    main(*sys.argv[1:])
