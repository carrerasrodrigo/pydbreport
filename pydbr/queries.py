#!/usr/bin/python
from send_email import send_email
from xml.etree import ElementTree as ET # or Alien??

import argparse
import csv
import datetime 
import MySQLdb
import os 

def scan_queries(path):
    ret = []
    for root, dirs, files in os.walk(os.path.join(path, "works")):
        for f in filter(lambda x: x.endswith(".xml"), files):
            p = os.path.join(root, f)
            with open(p, "r") as f:
                ret.append(ET.XML(f.read()))
    return ret

def run_query(dbName, user, password, host, query):
    db = MySQLdb.connect(host=host,
                     user=user,
                      passwd=password,
                      db=dbName)
    cur = db.cursor()
    cur.execute(query)

    rows = [[i[0] for i in cur.description]]
    for row in cur.fetchall():
        rows.append(row)
    db.close()

    return rows

def render_table(table):
    lines = []
    lines.append('<table style="border-color: #515151; border-style: solid; border-width: 1px;">')
    for row in table:
        r = '<tr>'
        for cell in row:
            r += '<td style="border-right-color: #515151; border-right-style: solid; border-right-width: 1px; min-width:300px">{0}</td>'.format(cell)
        r += "/<tr>"
        lines.append(r)
    lines.append("</table>")    

    return lines

def generate_csv(name, table):
    with open(name, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in table:
            writer.writerow(row)
    return name

def __day_is_ok(xml):
    # Tener en cuenta que el tag <day> tiene mayor prioridad que <weekday>
    day = datetime.datetime.now().day
    weekday = datetime.datetime.now().weekday()
    days = xml.find("day")
    weekdays = xml.find("weekday")
    
    if days is not None:
	l = days.text.replace(" ", "").split(",")
        return str(day) in l or "*" in l

    if weekdays is not None:
	l = weekdays.text.replace(" ", "").split(",")
        return str(weekday) in l or "*" in l

    return False

def process_xml(conf, xml):
    el = []
    csvs = []
    if not __day_is_ok(xml):
        # Ignores the xml files that we dont have to run that day
        return 
    for query in xml.find("./queries").getchildren():
        table = run_query(query.find("db_name").text,
            query.find("db_user").text,
            query.find("db_password").text,
            query.find("db_host").text,
            query.find("code").text
        )
        
        if query.find("transpose").text != "0":
            table = zip(*table)

        if query.find("csv").text != "0":
            csName = os.path.join(conf.basepath, "tmp", query.find("csv_name").text)
            cs = generate_csv(csName, table)
            csvs.append(cs)
        else:
            el.extend(render_table(table))
        
    emails = []
    if conf.output == "email":
        if args.emails is not None:
            emails = args.emails.split("|")
        else:
            for em in xml.findall("*/email"):
                emails.append(em.text)
        if len(emails) > 0:
            send_email(xml.find("sender").text, emails, 
                xml.find("subject").text,
                "".join(el), csvs, host=conf.smtp_host, port=conf.smtp_port)
    else:
        print_email_on_screen("".join(el), csvs)


parser = argparse.ArgumentParser(description="PyDbReport", add_help=True)
parser.add_argument("--output", help="email or screen. If it's email it will send the report by email otherwise will print it on the screen", default="email")
parser.add_argument("--emails", help="Ignores the list of emails added in the xml file and send to the indicated emails. Ex: ema1@compar.com|em@asd.com", default=None, required=False)
parser.add_argument("--xml", help="The path of the xml that you want to use. If it's not used the script will read all the *.xml from the works folder", default=None, required=False)
parser.add_argument("--reportpath", help="The default path of the project", default=None)
parser.add_argument("--smtp-host", help="The SMTP host", default="localhost", dest="smtp_host")
parser.add_argument("--smtp-port", help="The SMTP host port", default="25", dest="smtp_port")

def main(conf):
    conf = parser.parse_args()
    if conf.xml is None and conf.reportpath is None:
        print("Please use --xml or --reportpath")
        exit(1)
    
    if conf.xml is None:
        xmls = scan_queries(conf.reportpath)
    else:
        with open(conf.xml, "r") as f:
            xmls = [ET.XML(f.read())]

    for xml in xmls:
        process_xml(conf, xml)

if __name__ == '__main__':
    conf = parser.parse_args()
    main(conf)
