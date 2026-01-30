import email
from email import policy
from email.header import decode_header, make_header


class EmailParser:
    def __init__(self, email_policy=policy.default):
        self.policy = email_policy

    def parse_email(self, raw_bytes: bytes) -> dict:
        """
        Takes raw email bytes and returns a clean dictionary.
        Treating the email as an object rather than just a string.
        """
        msg = email.message_from_bytes(raw_bytes, policy=self.policy)

        subject = self._decode_str(msg.get("Subject"))
        sender = self._decode_str(msg.get("From"))
        date = msg.get("Date")

        text_parts = []
        html_parts = []
        attachments = []

        # Check if the email is a "container" holding multiple parts (text, html, files)
        if msg.is_multipart():
            # .walk() creates a generator that visits every part of the email tree
            for part in msg.walk():
                # skip container parts
                if part.is_multipart():
                    continue

                content_type = part.get_content_type()
                disposition = (
                    part.get_content_disposition()
                )  # e.g., "attachment" or "inline"

                # attachments
                if disposition == "attachment":
                    filename = part.get_filename()
                    if filename:
                        attachments.append(self._decode_str(filename))
                    continue

                # most emails have two versions: "text/plain" (raw text) and "text/html" (styling)
                if content_type == "text/plain":
                    text_parts.append(self._get_decoded_payload(part))

                elif content_type == "text/html":
                    html_parts.append(self._get_decoded_payload(part))
        else:
            # the email is just a single block of text with no attachments
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                text_parts.append(self._get_decoded_payload(msg))
            elif content_type == "text/html":
                html_parts.append(self._get_decoded_payload(msg))

        body = "\n".join(text_parts).strip() or "\n".join(html_parts).strip()

        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body,
            "attachments": attachments,
        }

    def _decode_str(self, value):
        """
        Decode RFC 2047 encoded email headers safely
        Email headers (like Subject) often look like: '=?utf-8?q?Hello?='
        This function converts them back into readable Unicode strings
        """
        if not value:
            return ""
        return str(make_header(decode_header(value)))

    def _get_decoded_payload(self, part):
        """
        Decode the raw binary payload of an email part into a Python string
        """
        payload = part.get_payload(decode=True)
        if not payload:
            return ""

        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="ignore")
        except LookupError:
            # unknown charset
            return payload.decode("utf-8", errors="ignore")
