# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pydbr"))

import asyncore
import threading
import unittest
import logging

from pydbr.queries import main, scan_queries, run_query, render_table
from smtpd import SMTPServer


class EmailServer(SMTPServer):
    messages = []
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        self.messages.append(data)

class PyDbRTest(unittest.TestCase):
    test_path = os.path.dirname(__file__)
    xml_test_cases = 2

    def setUp(self):
        # Compatibility with Python 2.6
        if getattr(self, "server_em", None) is None:
            self.setUpClass()

    @classmethod
    def setUpClass(cls):
        def start_server():
            cls.server_em = EmailServer(('localhost', 2525), None)
            asyncore.loop()
        cls.smtp_server = threading.Thread(target=start_server)
        cls.smtp_server.daemon = True
        cls.smtp_server.start()

    def test_no_args(self):
        self.assertRaises(Exception, main)
    
    #def test_print_screen(self):
    #    wp = os.path.join(self.test_path, "works", "test.xml")
    #    ar = ["--output=screen", "--xml={0}".format(wp)]
    #    self.assertTrue(main(*ar))
    
    def test_scan_queries(self):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        self.assertEqual(len(xmls), self.xml_test_cases)
        self.assertEqual(xmls[0].find("subject").text, "test report")

    def test_scan_queries_invalid_path(self):
        xmls = scan_queries("/nanana")
        self.assertEqual(len(xmls), 0)

    def test_run_query(self):
        query = run_query("pydbreport", "root", "admin", "localhost", 
            "select first_name, rating from famous_people limit 2;")
        self.assertEqual(len(query), 3)
        self.assertEqual(query[0][0], "first_name")
        
    def test_render_table(self):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        query = run_query("pydbreport", "root", "admin", "localhost", 
            "select first_name, rating from famous_people limit 2;")
        r = render_table(xmls[0].find("queries").find("query"), query)
        self.assertTrue("first_name" in r)
        self.assertTrue("rating" in r)
        self.assertTrue("<table" in r)

    def test_render_table(self):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        query = run_query("pydbreport", "root", "admin", "localhost", 
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
        self.assertTrue("first_name" in message)

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

    def test_reportpath(self):
        p = os.path.join(self.test_path, "works")
        arg = "--smtp-port=2525 --smtp-host=localhost --reportpath={0}".format(p)
        main(*arg.split(" "))
        self.assertEqual(len(self.server_em.messages), self.xml_test_cases)

if __name__ == '__main__':
    unittest.main()
