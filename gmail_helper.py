import os

from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": os.environ["GMAIL_CLIENT_ID"],
            "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=["https://www.googleapis.com/auth/gmail.send"],
)

creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("refresh_token:", creds.refresh_token)