import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def create_sheet(credential_path, csv_path, account_email_to_share_list):
    if len(account_email_to_share_list) == 0:
        raise ValueError(
            "You need to provide at least one email to share the Google Sheet"
        )

    # Authenticate and build the service
    credentials = service_account.Credentials.from_service_account_file(
        credential_path,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )
    drive_service = build("drive", "v3", credentials=credentials)
    sheets_service = build("sheets", "v4", credentials=credentials)

    # Create a new Google Sheet
    sheet = (
        sheets_service.spreadsheets()
        .create(body={"properties": {"title": os.path.basename(csv_path)}})
        .execute()
    )
    sheet_id = sheet["spreadsheetId"]

    # Upload the CSV file to the Google Sheet
    media = MediaFileUpload(csv_path, mimetype="text/csv", resumable=True)
    drive_service.files().update(fileId=sheet_id, media_body=media).execute()

    # Share the Google Sheet with the list of emails
    for email in account_email_to_share_list:
        drive_service.permissions().create(
            fileId=sheet_id,
            body={"type": "user", "role": "writer", "emailAddress": email},
            fields="id",
        ).execute()

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"
