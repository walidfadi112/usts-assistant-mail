
import base64
import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    """Authentifie l'utilisateur et retourne le client Gmail en lecture seule."""
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"Fichier OAuth introuvable : {CREDENTIALS_FILE}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )
        credentials = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(
            credentials.to_json(), encoding="utf-8"
        )

    return build(
        "gmail", "v1", credentials=credentials,
        cache_discovery=False,
    )


def _decode_body(payload):
    """Extrait le texte d'un message MIME, y compris les parties imbriquées."""
    mime_type = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data")

    if mime_type == "text/plain" and data:
        return base64.urlsafe_b64decode(data).decode(
            "utf-8", errors="replace"
        )

    parts = payload.get("parts", [])
    texts = [_decode_body(part) for part in parts]
    return "\n".join(text for text in texts if text).strip()


def list_recent_messages(max_results=10):
    """Récupère les messages récents depuis la boîte Gmail autorisée."""
    if not 1 <= max_results <= 100:
        raise ValueError("max_results doit être compris entre 1 et 100.")

    service = get_gmail_service()
    response = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results)
        .execute()
    )

    messages = []

    for item in response.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(userId="me", id=item["id"], format="full")
            .execute()
        )

        headers = {
            header["name"].lower(): header["value"]
            for header in message.get("payload", {}).get("headers", [])
        }

        body = _decode_body(message.get("payload", {}))

        messages.append({
            "gmail_message_id": message["id"],
            "gmail_thread_id": message["threadId"],
            "sender": headers.get("from", "Expéditeur inconnu"),
            "recipients": headers.get("to", ""),
            "subject": headers.get("subject", "(Sans objet)"),
            "body": body,
            "internal_date": message.get("internalDate"),
        })

    return messages
