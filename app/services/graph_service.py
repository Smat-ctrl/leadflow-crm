import os
import requests
import msal
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = "https://login.microsoftonline.com/common"

SCOPES = ["User.Read", "Mail.ReadWrite"]


def get_access_token(outlook_account=None):
    if not CLIENT_ID:
        raise ValueError("CLIENT_ID is missing. Add it to your .env file.")

    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY
    )

    token_options = {"scopes": SCOPES}
    if outlook_account:
        token_options["login_hint"] = outlook_account

    result = app.acquire_token_interactive(**token_options)

    if "access_token" not in result:
        raise ValueError(f"Could not get Microsoft access token: {result}")

    return result["access_token"]


def create_email_draft(to_email, subject, body, access_token):
    url = "https://graph.microsoft.com/v1.0/me/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    draft_data = {
        "subject": subject,
        "body": {
            "contentType": "Text",
            "content": body
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": to_email
                }
            }
        ]
    }

    response = requests.post(url, headers=headers, json=draft_data)

    if response.status_code != 201:
        raise ValueError(f"Draft failed: {response.status_code} {response.text}")

    return response.json()


def create_email_drafts(email_messages, subject, outlook_account=None):
    if not email_messages:
        raise ValueError("Generate email messages before creating drafts.")
    if not subject.strip():
        raise ValueError("Enter a subject before creating drafts.")

    access_token = get_access_token(outlook_account=outlook_account)
    drafts = []
    failures = []

    for email in email_messages:
        try:
            draft = create_email_draft(
                to_email=email["Email"],
                subject=subject,
                body=email["Message"],
                access_token=access_token,
            )
            drafts.append({
                "email": email["Email"],
                "id": draft.get("id"),
            })
        except ValueError as error:
            failures.append({
                "email": email["Email"],
                "error": str(error),
            })

    return {
        "drafts": drafts,
        "failures": failures,
    }
