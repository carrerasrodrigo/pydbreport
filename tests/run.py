# -*- coding: utf-8 -*-
import os
import unittest
import logging

from pydbr.queries import main, scan_queries, run_query, render_table

class PyDbRTest(unittest.TestCase):
    test_path = os.path.dirname(__file__)

    def test_no_args(self):
        self.assertRaises(Exception, main)
    
    def test_print_screen(self):
        wp = os.path.join(self.test_path, "works", "test.xml")
        ar = ["--output=screen", "--xml={0}".format(wp)]
        self.assertTrue(main(*ar))
    
    def test_scan_queries(self):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        self.assertEqual(len(xmls), 1)
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
        query = run_query("pydbreport", "root", "admin", "localhost", 
            "select first_name, rating from famous_people limit 2;")
        r = render_table(query)
        self.assertFalse("first_name" in r)
        self.assertFalse("rating" in r)
        self.assertFalse("<table>" in r)

if __name__ == '__main__':
    unittest.main()
