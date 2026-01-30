import imaplib
import logging
import os
from dotenv import load_dotenv

load_dotenv()


class IMAPClientError(Exception):
    """Erreur générique IMAP"""

    pass


class IMAPClient:
    def __init__(self):
        self.server = os.getenv("IMAP_SERVER")
        self.port = int(os.getenv("IMAP_PORT", 993))
        self.email = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.conn = None

        if not all([self.server, self.email, self.password]):
            raise IMAPClientError("Configuration IMAP incomplète")

    # Connexion

    def connect(self):
        try:
            logging.info("Connecting to IMAP server...")
            self.conn = imaplib.IMAP4_SSL(self.server, self.port)
            self.conn.login(self.email, self.password)
            logging.info("IMAP connection established")
        except imaplib.IMAP4.error as e:
            logging.error("IMAP authentication failed", exc_info=True)
            raise IMAPClientError("IMAP authentication failed") from e

    def logout(self):
        if self.conn:
            logging.info("Logging out from IMAP")
            self.conn.logout()
            self.conn = None

    # Mailbox

    def select_mailbox(self, mailbox="INBOX"):
        self._ensure_connection()
        status, _ = self.conn.select(mailbox)
        if status != "OK":
            raise IMAPClientError(f"Cannot select mailbox: {mailbox}")

    # Search

    def search(self, criteria="ALL"):
        self._ensure_connection()
        status, messages = self.conn.search(None, criteria)
        if status != "OK":
            raise IMAPClientError("Search failed")
        return messages[0].split()

    # Fetch

    def fetch_email(self, email_id):
        self._ensure_connection()
        try:
            status, data = self.conn.fetch(email_id, "(RFC822)")
            if status != "OK":
                raise IMAPClientError("Fetch failed")
            return data[0][1]
        except imaplib.IMAP4.abort:
            logging.warning("IMAP connection aborted, reconnecting...")
            self._reconnect()
            return self.fetch_email(email_id)

    # Flags / actions

    def mark_as_read(self, email_id):
        self._ensure_connection()
        self.conn.store(email_id, "+FLAGS", "\\Seen")

    # Internals

    def _ensure_connection(self):
        if not self.conn:
            raise IMAPClientError("IMAP not connected")

    def _reconnect(self):
        self.logout()
        self.connect()

    # Context manager

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.logout()
