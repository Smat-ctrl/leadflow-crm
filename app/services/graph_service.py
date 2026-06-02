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

# Use common so personal Outlook accounts and school/work Microsoft accounts can sign in.
# School accounts may still require admin approval depending on the university.
AUTHORITY = "https://login.microsoftonline.com/common"

# Mail.ReadWrite is needed to create drafts in Outlook.
SCOPES = ["User.Read", "Mail.ReadWrite"]


def get_public_client_app():
    if msal is None:
        raise ValueError(
            "The msal package is not installed. Run: pip install msal requests python-dotenv"
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
        error_description = result.get("error_description", "")
        error = result.get("error", "")

        if (
            "AADSTS65001" in error_description
            or "admin" in error_description.lower()
            or "consent" in error_description.lower()
        ):
            raise ValueError(
                "Authentication failed because this Microsoft account's organization "
                "requires admin approval before LeadCRM Flow can access Outlook drafts. "
                "Try a personal Outlook account, or ask your school/work IT admin to approve the app."
            )

        raise ValueError(f"Could not get Microsoft access token: {error or error_description or result}")

    return result["access_token"]


def get_signed_in_user(access_token):
    url = "https://graph.microsoft.com/v1.0/me?$select=displayName,mail,userPrincipalName"

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise ValueError(
            f"Could not check signed-in Microsoft account: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


def validate_signed_in_account(access_token, expected_account):
    signed_in_user = get_signed_in_user(access_token)

    expected = expected_account.strip().lower()

    signed_in_addresses = [
        signed_in_user.get("mail"),
        signed_in_user.get("userPrincipalName"),
    ]

    signed_in_addresses = [
        address.lower()
        for address in signed_in_addresses
        if address
    ]

    if expected and expected not in signed_in_addresses:
        actual = signed_in_user.get("mail") or signed_in_user.get("userPrincipalName")

        raise ValueError(
            f"You signed in as {actual}, but entered {expected_account}. "
            "Sign in with the same Microsoft account you entered."
        )

    return signed_in_user


def create_email_draft(to_email, subject, body, access_token):
    if not to_email or "@" not in to_email:
        raise ValueError(f"Invalid recipient email: {to_email}")

    if not subject.strip():
        raise ValueError("Email subject cannot be empty.")

    if not body.strip():
        raise ValueError(f"Email body for {to_email} cannot be empty.")

    url = "https://graph.microsoft.com/v1.0/me/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    draft_data = {
        "subject": subject,
        "body": {
            "contentType": "Text",
            "content": body,
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": to_email,
                }
            }
        ],
    }

    response = requests.post(url, headers=headers, json=draft_data)

    if response.status_code != 201:
        raise ValueError(f"Draft failed for {to_email}: {response.status_code} {response.text}")

    return response.json()


def create_email_drafts(email_messages, subject, access_token, expected_account=None):
    if not email_messages:
        raise ValueError("Generate email messages before creating drafts.")

    if not subject.strip():
        raise ValueError("Enter a subject before creating drafts.")

    if not access_token:
        raise ValueError("Sign in with Microsoft before creating drafts.")

    signed_in_user = None

    if expected_account:
        signed_in_user = validate_signed_in_account(access_token, expected_account)

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

            drafts.append(
                {
                    "email": email["Email"],
                    "id": draft.get("id"),
                }
            )

        except Exception as error:
            failures.append(
                {
                    "email": email.get("Email", "Unknown email"),
                    "error": str(error),
                }
            )

    return {
        "drafts": drafts,
        "failures": failures,
        "signed_in_user": signed_in_user,
    }
