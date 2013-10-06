# -*- coding: utf-8 -*-
import os
import unittest
import logging

from pydbr.queries import main

class PyDbRTest(unittest.TestCase):
    test_path = os.path.dirname(__file__)

    def test_init(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
