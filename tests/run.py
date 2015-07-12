# -*- coding: utf-8 -*-
import os
import sys
py3 = sys.version_info[0] == 3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pydbr"))

import asyncore
import base64
import datetime
import email
import time
import threading
import unittest
import sqlalchemy
from pydbr.queries import main, scan_queries, run_query, render_table
from smtpd import SMTPServer


class EmailServer(SMTPServer):
    messages = []

    def process_message(self, peer, mailfrom, rcpttos, data):
        self.messages.append(data)

    @classmethod
    def dec(cls, message):
        b64 = email.message_from_string(message).get_payload()[0].get_payload()
        return base64.b64decode(b64)


class PyDbRTest(unittest.TestCase):
    test_path = os.path.dirname(__file__)

    def setUp(self):
        self.server_em.messages = []
        os.environ['DB_NAME'] = 'pydbreport'
        os.environ['DB_USER'] = 'pydbreport'
        os.environ['DB_PASSWORD'] = ''
        os.environ['DB_HOST'] = 'localhost'

    @classmethod
    def setUpClass(cls):
        def start_server():
            cls.server_em = EmailServer(('localhost', 2525), None)
            asyncore.loop()
        print("Starting SMTP Server")
        cls.smtp_server = threading.Thread(target=start_server)
        cls.smtp_server.daemon = True
        cls.smtp_server.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        elog = os.path.join(cls.test_path, 'works_error', 'pydbr.log')
        if os.path.isfile(elog):
            os.remove(elog)

    @property
    def xml_test_cases(self):
        total = 0
        path = os.path.join(self.test_path, "works")
        for root, dirs, files in os.walk(path):
            for f in filter(lambda x: x.endswith(".xml"), files):
                total += 1
        return total

    def test_no_args(self):
        self.assertRaises(Exception, main)

    def test_scan_queries(self):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        self.assertEqual(len(xmls), self.xml_test_cases)
        self.assertEqual(xmls[0].find("subject").text, "test report")

    def test_scan_queries_invalid_path(self):
        xmls = scan_queries("/nanana")
        self.assertEqual(len(xmls), 0)

    def test_run_query(self):
        query = run_query("mysql+pymysql", "pydbreport", "pydbreport",
            "", "localhost", None,
            "select first_name, rating from famous_people limit 2;")
        self.assertEqual(len(query), 3)
        self.assertEqual(query[0][0], "first_name")

    def test_run_query_sqlite(self):
        db_name = os.path.join(os.path.dirname(__file__), 'test.db')
        query = run_query("sqlite", db_name, None, None, None, None,
            "select first_name, rating from famous_people limit 2;")
        self.assertEqual(len(query), 3)
        self.assertEqual(query[0][0], "first_name")

    def test_render_table(self):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        query = run_query("mysql+pymysql", "pydbreport", "pydbreport",
            "", "localhost", None,
            "select first_name, rating from famous_people limit 2;")

        r = render_table(xmls[0].find("queries").find("query"), query)
        self.assertTrue("first_name" in r)
        self.assertTrue("rating" in r)
        self.assertTrue("<table" in r)

    def test_run_report(self):
        p = os.path.join(self.test_path, "works", "test_no_csv.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0}".format(p)
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        self.assertTrue("From: sender@test.com" in message)
        self.assertTrue("To: test@t.com" in message)

    def test_emails(self):
        p = os.path.join(self.test_path, "works", "test_no_csv.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(p)
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        self.assertTrue("To: noemail@email.com" in message)

    def test_bcc_cc(self):
        p = os.path.join(self.test_path, "works", "test_no_csv.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0}".format(p)
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        self.assertTrue("To: test@t.com" in message)
        self.assertTrue("Bcc: bcc@bcc.com" in message)
        self.assertTrue("Cc: cc@cc.com" in message)

    def test_variables(self):
        p = os.path.join(self.test_path, "works", "test_variables.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0}".format(p)
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        if not py3:
            message = self.server_em.dec(message)
        self.assertTrue("hallo_test" in str(message))
        self.assertTrue("Luke" in str(message))

    def test_reportpath(self):
        p = os.path.join(self.test_path, "works")
        arg = "--smtp-port=2525 --smtp-host=localhost --reportpath={0}".format(p)
        main(*arg.split(" "))
        self.assertEqual(len(self.server_em.messages), self.xml_test_cases - 2)

    def test_day_hour(self):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml: t = xml.read()
        t = t.replace("REPLACE_DAY", str(datetime.datetime.now().day))
        t = t.replace("REPLACE_HOUR", str(datetime.datetime.now().hour))
        with open(p2, "w") as xml: xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(p2)
        main(*arg.split(" "))
        self.assertEqual(1, len(self.server_em.messages))

    def test_day_hour_wrong(self):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml: t = xml.read()
        t = t.replace("REPLACE_DAY", str(datetime.datetime.now().day))
        t = t.replace("REPLACE_HOUR", str(datetime.datetime.now().hour + 1))
        with open(p2, "w") as xml: xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(p2)
        main(*arg.split(" "))
        self.assertEqual(0, len(self.server_em.messages))

    def test_day_wrong_hour(self):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml: t = xml.read()
        t = t.replace("REPLACE_DAY", str(datetime.datetime.now().day + 1))
        t = t.replace("REPLACE_HOUR", str(datetime.datetime.now().hour))
        with open(p2, "w") as xml: xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(p2)
        main(*arg.split(" "))
        self.assertEqual(0, len(self.server_em.messages))

    def test_day_hour_wildcard(self):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml: t = xml.read()
        t = t.replace("REPLACE_DAY", "*")
        t = t.replace("REPLACE_HOUR", "*")
        with open(p2, "w") as xml: xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(p2)
        main(*arg.split(" "))
        self.assertEqual(1, len(self.server_em.messages))

    def test_empty_email_no(self):
        p = os.path.join(self.test_path, "works", "test_empty_email_no.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(p)
        main(*arg.split(" "))
        self.assertEqual(0, len(self.server_em.messages))

    def test_empty_email_yes(self):
        p = os.path.join(self.test_path, "works", "test_empty_email_yes.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(p)
        main(*arg.split(" "))
        self.assertEqual(1, len(self.server_em.messages))

    def test_error_log(self):
        p = os.path.join(self.test_path, "works_error", "test_error.xml")
        elog = os.path.join(self.test_path, "works_error")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com --log-folder={1}".format(p, elog)
        f = lambda: main(*arg.split(" "))
        self.assertRaises(sqlalchemy.exc.ProgrammingError, f)
        with open(os.path.join(elog, 'pydbr.log')) as ff:
            self.assertTrue('error query' in ff.read())

    def test_error_log_sqlite(self):
        p = os.path.join(self.test_path, "works_error", "test_error_sqlite.xml")
        elog = os.path.join(self.test_path, "works_error")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com --log-folder={1}".format(p, elog)
        f = lambda: main(*arg.split(" "))
        self.assertRaises(sqlalchemy.exc.OperationalError, f)
        with open(os.path.join(elog, 'pydbr.log')) as ff:
            self.assertTrue('error query' in ff.read())



if __name__ == '__main__':
    unittest.main()
