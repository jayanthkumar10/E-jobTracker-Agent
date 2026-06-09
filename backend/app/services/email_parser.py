import base64
import email
from email.utils import parseaddr
import re
from datetime import datetime

class EmailParser:
    @staticmethod
    def decode_base64(data: str) -> str:
        """Decodes Google Gmail base64url encoded strings."""
        try:
            decoded_bytes = base64.urlsafe_b64decode(data.encode('ASCII'))
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception:
            return ""

    @classmethod
    def get_email_body(cls, payload: dict) -> tuple[str, str]:
        """
        Recursively parses email parts to return (plain_text, html_text).
        Gmail API payloads can be nested multiparts.
        """
        body_text = ""
        body_html = ""

        mime_type = payload.get("mimeType", "")
        parts = payload.get("parts", [])
        body_data = payload.get("body", {}).get("data", "")

        if mime_type == "text/plain" and body_data:
            body_text = cls.decode_base64(body_data)
        elif mime_type == "text/html" and body_data:
            body_html = cls.decode_base64(body_data)
        
        # If it's multipart, recursively parse children
        for part in parts:
            part_text, part_html = cls.get_email_body(part)
            if part_text:
                body_text += "\n" + part_text
            if part_html:
                body_html += "\n" + part_html
                
        return body_text.strip(), body_html.strip()

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Removes excess whitespaces, links, and formatting to clean text for LLM parsing."""
        if not text:
            return ""
        
        # Replace multiple spaces/newlines with single ones
        text = re.sub(r'\s+', ' ', text)
        # Limit total characters to fit context limits (200k chars)
        text = text[:150000]
        return text.strip()

    @classmethod
    def parse_gmail_message(cls, message_payload: dict) -> dict:
        """
        Parses a full Gmail API message object into structured metadata and content.
        """
        headers = message_payload.get("payload", {}).get("headers", [])
        
        subject = ""
        sender = ""
        recipient = ""
        date_str = ""
        
        for header in headers:
            name = header.get("name", "").lower()
            value = header.get("value", "")
            if name == "subject":
                subject = value
            elif name == "from":
                sender = value
            elif name == "to":
                recipient = value
            elif name == "date":
                date_str = value

        # Clean sender/recipient fields to get just the email address
        _, sender_email = parseaddr(sender)
        _, recipient_email = parseaddr(recipient)
        
        # Parse received date
        received_at = datetime.utcnow()
        if date_str:
            try:
                # Remove timezone strings if present in non-standard formats
                clean_date = date_str.split(" (")[0]
                parsed_date = email.utils.parsedate_to_datetime(clean_date)
                received_at = parsed_date.astimezone(datetime.utcnow().astimezone().tzinfo).replace(tzinfo=None)
            except Exception:
                pass # Fallback to current time
        
        body_text, body_html = cls.get_email_body(message_payload.get("payload", {}))
        
        # If we got absolutely nothing, check structural fallback
        if not body_text and not body_html:
            snippet = message_payload.get("snippet", "")
            body_text = snippet

        return {
            "gmail_message_id": message_payload.get("id"),
            "gmail_thread_id": message_payload.get("threadId"),
            "subject": subject,
            "sender_email": sender_email,
            "recipient_email": recipient_email,
            "received_at": received_at,
            "body_text": cls.clean_text(body_text),
            "body_html": body_html
        }
