# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pydbr"))


import asyncore
import base64
import datetime
import email
import os
import threading
import time
import unittest
from smtpd import SMTPServer
from unittest.mock import MagicMock, patch

import pytz
import sqlalchemy
from croniter import croniter
from gdrive import create_sheet

from pydbr.queries import main, render_table, run_query, scan_queries
from pydbr.schedulerconf import Scheduler, Task


class EmailServer(SMTPServer):
    messages = []

    def process_message(self, peer, mailfrom, rcpttos, data, *agrs, **kwargs):
        self.messages.append(data)

    @classmethod
    def dec(cls, message):
        b64 = email.message_from_string(message).get_payload()[0].get_payload()
        return base64.b64decode(b64)


@patch(
    "pydbr.queries.create_sheet",
    ret_value=[dict(name="x", link="https://example.com")],
)
class PyDbRTest(unittest.TestCase):
    test_path = os.path.dirname(__file__)

    def setUp(self):
        self.server_em.messages = []
        os.environ["DB_NAME"] = "pydbreport"
        os.environ["DB_USER"] = "root"
        os.environ["DB_PASSWORD"] = "root"
        os.environ["DB_HOST"] = "127.0.0.1"

    @classmethod
    def setUpClass(cls):
        def start_server():
            cls.server_em = EmailServer(("localhost", 2525), None)
            asyncore.loop()

        print("Starting SMTP Server")
        cls.smtp_server = threading.Thread(target=start_server)
        cls.smtp_server.daemon = True
        cls.smtp_server.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        elog = os.path.join(cls.test_path, "works_error", "pydbr.log")
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

    def test_no_args(self, *args, **kwargs):
        self.assertRaises(Exception, main)

    def test_scan_queries(self, *args, **kwargs):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        self.assertEqual(len(xmls), self.xml_test_cases)
        self.assertEqual(xmls[0].find("subject").text, "test report")

    def test_scan_queries_invalid_path(self, *args, **kwargs):
        xmls = scan_queries("/nanana")
        self.assertEqual(len(xmls), 0)

    def test_run_query(self, *args, **kwargs):
        query = run_query(
            "mysql+pymysql",
            "pydbreport",
            "root",
            "root",
            "127.0.0.1",
            None,
            "select first_name, rating from famous_people limit 2;",
        )
        self.assertEqual(len(query), 3)
        self.assertIn("first_name", query[0])

    def test_run_query_sqlite(self, *args, **kwargs):
        db_name = os.path.join(os.path.dirname(__file__), "test.db")
        query = run_query(
            "sqlite",
            db_name,
            None,
            None,
            None,
            None,
            "select first_name, rating from famous_people limit 2;",
        )
        self.assertEqual(len(query), 3)
        self.assertIn("first_name", query[0])

    def test_render_table(self, *args, **kwargs):
        xmls = scan_queries(os.path.join(self.test_path, "works"))
        query = run_query(
            "mysql+pymysql",
            "pydbreport",
            "root",
            "root",
            "127.0.0.1",
            None,
            "select first_name, rating from famous_people limit 2;",
        )

        r = render_table(xmls[0].find("queries").find("query"), query)
        self.assertTrue("first_name" in r)
        self.assertTrue("rating" in r)
        self.assertTrue("<table" in r)

    def test_run_report(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_no_csv.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0}".format(p)
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        self.assertTrue(b"From: sender@test.com" in message)
        self.assertTrue(b"To: test@t.com" in message)

    def test_emails(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_no_csv.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p
        )
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        self.assertTrue(b"To: noemail@email.com" in message)

    def test_bcc_cc(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_no_csv.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0}".format(p)
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        self.assertTrue(b"To: test@t.com" in message)
        self.assertTrue(b"Bcc: bcc@bcc.com" in message)
        self.assertTrue(b"Cc: cc@cc.com" in message)

    def test_variables(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_variables.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0}".format(p)
        main(*arg.split(" "))
        message = self.server_em.messages.pop()
        self.assertTrue("hallo_test" in str(message))
        self.assertTrue("Luke" in str(message))

    def test_reportpath(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works")
        arg = "--smtp-port=2525 --smtp-host=localhost --reportpath={0}".format(
            p
        )
        main(*arg.split(" "))
        self.assertEqual(len(self.server_em.messages), self.xml_test_cases - 3)

    def test_day_hour(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml:
            t = xml.read()
        t = t.replace("REPLACE_DAY", str(datetime.datetime.now().day))
        t = t.replace("REPLACE_HOUR", str(datetime.datetime.now().hour))
        with open(p2, "w") as xml:
            xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p2
        )
        main(*arg.split(" "))
        self.assertEqual(1, len(self.server_em.messages))

    def test_day_hour_wrong(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml:
            t = xml.read()
        t = t.replace("REPLACE_DAY", str(datetime.datetime.now().day))
        t = t.replace("REPLACE_HOUR", str(datetime.datetime.now().hour + 1))
        with open(p2, "w") as xml:
            xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p2
        )
        main(*arg.split(" "))
        self.assertEqual(0, len(self.server_em.messages))

    def test_day_wrong_hour(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml:
            t = xml.read()
        t = t.replace("REPLACE_DAY", str(datetime.datetime.now().day + 1))
        t = t.replace("REPLACE_HOUR", str(datetime.datetime.now().hour))
        with open(p2, "w") as xml:
            xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p2
        )
        main(*arg.split(" "))
        self.assertEqual(0, len(self.server_em.messages))

    def test_day_hour_wildcard(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_time_to_send.xml")
        p2 = os.path.join(self.test_path, "works", "test_time_to_send.repxml")
        with open(p) as xml:
            t = xml.read()
        t = t.replace("REPLACE_DAY", "*")
        t = t.replace("REPLACE_HOUR", "*")
        with open(p2, "w") as xml:
            xml.write(t)

        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p2
        )
        main(*arg.split(" "))
        self.assertEqual(1, len(self.server_em.messages))

    def test_empty_email_no(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_empty_email_no.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p
        )
        main(*arg.split(" "))
        self.assertEqual(0, len(self.server_em.messages))

    def test_empty_email_yes(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_empty_email_yes.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p
        )
        main(*arg.split(" "))
        self.assertEqual(1, len(self.server_em.messages))

    def test_google_sheet(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_google_sheet.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p
        )
        with patch(
            "pydbr.queries.create_sheet",
            ret_value=[dict(name="x", link="https://example.com")],
        ) as fn:
            main(*arg.split(" "))
            self.assertTrue(fn.called)

    def test_query_with_no_select(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works", "test_update_query.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com".format(
            p
        )

        total1 = run_query(
            "mysql+pymysql",
            "pydbreport",
            "root",
            "root",
            "127.0.0.1",
            None,
            "select count(*) from famous_people where first_name = 'test'",
        )[1][0]
        main(*arg.split(" "))
        total2 = run_query(
            "mysql+pymysql",
            "pydbreport",
            "root",
            "root",
            "127.0.0.1",
            None,
            "select count(*) from famous_people where first_name = 'test'",
        )[1][0]

        self.assertEqual(total1 + 1, total2)

    def test_error_log(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works_error", "test_error.xml")
        elog = os.path.join(self.test_path, "works_error")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com --log-folder={1}".format(
            p, elog
        )
        f_lambda = lambda: main(*arg.split(" "))
        self.assertRaises(sqlalchemy.exc.ProgrammingError, f_lambda)
        with open(os.path.join(elog, "pydbr.log")) as ff:
            self.assertTrue("error query" in ff.read())

    def test_error_log_sqlite(self, *args, **kwargs):
        p = os.path.join(self.test_path, "works_error", "test_error_sqlite.xml")
        elog = os.path.join(self.test_path, "works_error")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --emails=noemail@email.com --log-folder={1}".format(
            p, elog
        )
        f_lambda = lambda: main(*arg.split(" "))
        self.assertRaises(sqlalchemy.exc.OperationalError, f_lambda)
        with open(os.path.join(elog, "pydbr.log")) as ff:
            self.assertTrue("error query" in ff.read())

    def test_scheduler(self, *args, **kwargs):
        tz = pytz.timezone("UTC")
        base = tz.localize(datetime.datetime.now()) - datetime.timedelta(
            minutes=10
        )

        scheduler = Scheduler()
        cron = croniter("* * * * *", base)

        def execute():
            pass

        task = Task(cron, execute, [], "task name")
        scheduler.add_task(task)

        self.assertEqual(len(scheduler.tasks), 1)
        self.assertTrue(task.should_execute())
        exe1 = task.next_iter
        task.execute()
        self.assertTrue(exe1 < task.next_iter)

    def test_scheduler_loop(self, *args, **kwargs):
        def execute(*args):
            pass

        p = os.path.join(self.test_path, "works", "test_beat.xml")
        arg = "--smtp-port=2525 --smtp-host=localhost --xml={0} --beat --emails=noemail@email.com".format(
            p
        )
        with patch("pydbr.schedulerconf.Scheduler.loop") as f:
            main(*arg.split(" "))
            self.assertTrue(f.called)


class TestGDrive(unittest.TestCase):

    @patch("gdrive.service_account.Credentials.from_service_account_file")
    @patch("gdrive.build")
    @patch("gdrive.MediaFileUpload")
    def test_create_sheet_success(
        self, mock_media_file_upload, mock_build, mock_credentials
    ):
        # Mock the credentials
        mock_credentials.return_value = MagicMock()

        # Mock the drive and sheets services
        mock_drive_service = MagicMock()
        mock_sheets_service = MagicMock()
        mock_build.side_effect = lambda service, version, credentials: {
            "drive": mock_drive_service,
            "sheets": mock_sheets_service,
        }[service]

        # Mock the creation of the sheet
        mock_sheets_service.spreadsheets.return_value.create.return_value.execute.return_value = {
            "spreadsheetId": "test_sheet_id"
        }

        # Mock the file upload
        mock_media_file_upload.return_value = MagicMock()

        # Mock the file update
        mock_drive_service.files.return_value.update.return_value.execute.return_value = (
            {}
        )

        # Mock the permissions creation
        mock_drive_service.permissions.return_value.create.return_value.execute.return_value = (
            {}
        )

        # Define test inputs
        credential_path = "path/to/credentials.json"
        csv_path = "path/to/file.csv"
        account_email_to_share_list = [
            "email1@example.com",
            "email2@example.com",
        ]

        # Call the function
        result = create_sheet(
            credential_path, csv_path, account_email_to_share_list
        )

        # Assertions
        self.assertEqual(
            result, "https://docs.google.com/spreadsheets/d/test_sheet_id"
        )
        mock_credentials.assert_called_once_with(
            credential_path,
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/spreadsheets",
            ],
        )
        mock_build.assert_any_call(
            "drive", "v3", credentials=mock_credentials.return_value
        )
        mock_build.assert_any_call(
            "sheets", "v4", credentials=mock_credentials.return_value
        )
        mock_sheets_service.spreadsheets.return_value.create.assert_called_once_with(
            body={"properties": {"title": os.path.basename(csv_path)}}
        )
        mock_drive_service.files.return_value.update.assert_called_once()
        mock_drive_service.permissions.return_value.create.assert_called()

    @patch("gdrive.service_account.Credentials.from_service_account_file")
    @patch("gdrive.build")
    def test_create_sheet_invalid_credentials(
        self, mock_build, mock_credentials
    ):
        # Mock the credentials to raise an exception
        mock_credentials.side_effect = Exception("Invalid credentials")

        # Define test inputs
        credential_path = "path/to/invalid_credentials.json"
        csv_path = "path/to/file.csv"
        account_email_to_share_list = [
            "email1@example.com",
            "email2@example.com",
        ]

        # Call the function and assert it raises an exception
        with self.assertRaises(Exception) as context:
            create_sheet(credential_path, csv_path, account_email_to_share_list)
        self.assertTrue("Invalid credentials" in str(context.exception))

    @patch("gdrive.service_account.Credentials.from_service_account_file")
    @patch("gdrive.build")
    def test_create_sheet_missing_csv(self, mock_build, mock_credentials):
        # Mock the credentials
        mock_credentials.return_value = MagicMock()

        # Define test inputs
        credential_path = "path/to/credentials.json"
        csv_path = "path/to/missing_file.csv"
        account_email_to_share_list = [
            "email1@example.com",
            "email2@example.com",
        ]

        # Call the function and assert it raises an exception
        with self.assertRaises(FileNotFoundError):
            create_sheet(credential_path, csv_path, account_email_to_share_list)

    @patch("gdrive.service_account.Credentials.from_service_account_file")
    @patch("gdrive.build")
    @patch("gdrive.MediaFileUpload")
    def test_create_sheet_empty_email_list(
        self, mock_media_file_upload, mock_build, mock_credentials
    ):
        # Mock the credentials
        mock_credentials.return_value = MagicMock()

        # Mock the drive and sheets services
        mock_drive_service = MagicMock()
        mock_sheets_service = MagicMock()
        mock_build.side_effect = lambda service, version, credentials: {
            "drive": mock_drive_service,
            "sheets": mock_sheets_service,
        }[service]

        # Mock the creation of the sheet
        mock_sheets_service.spreadsheets.return_value.create.return_value.execute.return_value = {
            "spreadsheetId": "test_sheet_id"
        }

        # Mock the file upload
        mock_media_file_upload.return_value = MagicMock()

        # Mock the file update
        mock_drive_service.files.return_value.update.return_value.execute.return_value = (
            {}
        )

        # Define test inputs
        credential_path = "path/to/credentials.json"
        csv_path = "path/to/file.csv"
        account_email_to_share_list = []

        # Call the function and assert it raises an exception
        with self.assertRaises(ValueError) as context:
            create_sheet(credential_path, csv_path, account_email_to_share_list)
        self.assertTrue(
            "You need to provide at least one email to share the Google Sheet"
            in str(context.exception)
        )


if __name__ == "__main__":
    unittest.main()
