import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from openai import OpenAI

with open("openai_tok.json", "r") as token:
  api_tok = json.load(token)["Token"]

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]
creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists("token.json"):
  creds = Credentials.from_authorized_user_file("token.json", SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
  else:
    flow = InstalledAppFlow.from_client_secrets_file(
      "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
  # Save the credentials for the next run
  with open("token.json", "w") as token:
    token.write(creds.to_json())

def gmail_send_message(email: str, name: str, date: str, title: str, description: str):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id
    """
    url = "https://jamsapi.hackclub.dev/openai"

    client = OpenAI(
        # This is the default and can be omitted
        api_key=api_tok, base_url=url,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a secretary who writes emails for people. Do not include any placeholders or unnecessary information."
            },
            {
                "role": "user",
                "content": f"Create the body of an email to {name} inviting them to an event at {date}, {title} - {description}. The sender's name is Revis. Do not include any placeholders.",
            },
        ],
        model="gpt-3.5-turbo"
    )
    print(chat_completion.choices[0].message.content)
    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()

        message.set_content(chat_completion.choices[0].message.content)

        message["To"] = email
        message["Subject"] = "Automated draft"

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        # pylint: disable=E1101
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None
    return send_message




gmail_send_message("testing@gmail.com", "John", "July 30 2024", "Meeting with Reed", "Meet with me about the new product")