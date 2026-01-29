import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
print("✅ Connecté au serveur IMAP")


mail.select("INBOX")


status, messages = mail.search(None, "UNSEEN")
email_ids = messages[0].split()
print(f"📨 {len(email_ids)} emails non lus")


for eid in email_ids[-5:]:
    status, data = mail.fetch(eid, "(RFC822)")
    raw_email = data[0][1]
    msg = email.message_from_bytes(raw_email)

    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8", errors="ignore")
    status, data = mail.fetch(eid, "(INTERNALDATE)")
    print(data)

    sender = msg.get("From")
    date = msg.get("Date")
    print(f"✉️ {sender} | {subject} | {date}")


mail.logout()
print(" Deconnection")
