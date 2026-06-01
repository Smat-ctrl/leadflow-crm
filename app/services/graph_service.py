import os
import requests

try:
    import msal
except ImportError:
    msal = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = "https://login.microsoftonline.com/common"

SCOPES = ["User.Read", "Mail.ReadWrite"]


def get_public_client_app():
    if msal is None:
        raise ValueError(
            "The msal package is not installed. Add msal to requirements.txt "
            "and redeploy the app."
        )
    if not CLIENT_ID:
        raise ValueError("CLIENT_ID is missing. Add it to your .env file.")

    return msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY
    )


def start_device_login(microsoft_account=None):
    app = get_public_client_app()
    if microsoft_account:
        try:
            flow = app.initiate_device_flow(
                scopes=SCOPES,
                login_hint=microsoft_account,
            )
        except TypeError:
            flow = app.initiate_device_flow(scopes=SCOPES)
    else:
        flow = app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        raise ValueError(f"Could not start Microsoft sign-in: {flow}")

    return flow


def get_access_token_from_device_login(device_flow):
    if not device_flow:
        raise ValueError("Start Microsoft sign-in before creating drafts.")

    app = get_public_client_app()
    result = app.acquire_token_by_device_flow(device_flow)

    if "access_token" not in result:
        error = result.get("error_description") or result
        raise ValueError(f"Could not get Microsoft access token: {error}")

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


def create_email_drafts(email_messages, subject, access_token):
    if not email_messages:
        raise ValueError("Generate email messages before creating drafts.")
    if not subject.strip():
        raise ValueError("Enter a subject before creating drafts.")
    if not access_token:
        raise ValueError("Sign in with Microsoft before creating drafts.")

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
