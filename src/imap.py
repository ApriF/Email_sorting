import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT"))
EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

def connect_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL, PASSWORD)
        print("✅ Connexion IMAP réussie")
        return mail
    except imaplib.IMAP4.error as e:
        print("❌ Erreur IMAP :", e)
        return None

if __name__ == "__main__":
    imap = connect_imap()
    if imap:
        imap.logout()
