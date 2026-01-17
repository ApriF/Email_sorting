from imap.client import IMAPClient, IMAPClientError
from utils.logger import setup_logger
import logging

def main():
    setup_logger()
    logging.info("Starting email ingestion pipeline")

    try:
        with IMAPClient() as client:
            client.select_mailbox("INBOX")

            email_ids = client.search("UNSEEN")
            logging.info(f"{len(email_ids)} unread emails found")

            for email_id in email_ids:
                raw_email = client.fetch_email(email_id)

                # Pour l’instant : simple preuve que ça marche
                logging.info(f"Email {email_id.decode()} fetched")

                # Plus tard :
                # parser.process(raw_email)
                # client.mark_as_read(email_id)

    except IMAPClientError as e:
        logging.error(f"IMAP pipeline failed: {e}")
    except Exception as e:
        logging.exception("Unexpected error occurred")

    logging.info("Email ingestion pipeline finished")


if __name__ == "__main__":
    main()
