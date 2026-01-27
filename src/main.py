from imap.client import IMAPClient, IMAPClientError
from utils.logger import setup_logger
import logging

import parser.email_parser as parser
import parser.classification as category

def main():
    setup_logger()
    logging.info("Starting email ingestion pipeline")

    try:
        with IMAPClient() as client:
            client.select_mailbox("INBOX")

            email_ids = client.search("UNSEEN")
            logging.info(f"{len(email_ids)} unread emails found")

            for email_id in email_ids:
                try:
                    raw_email = client.fetch_email(email_id)

                    # Pour l’instant : simple preuve que ça marche
                    logging.info(f"Email {email_id.decode()} fetched")

                    # Plus tard :
                    email_data = parser.parse_email(raw_email)
                    email_category = category.classify_email(email_data)

                    logging.info(f"Sender: {email_data['sender']}")
                    logging.info(f"Subject: {email_data['subject']}")
                    logging.info(f"Date: {email_data['date']}")
                    logging.info(f"Category: {email_category}")

                    # logging.info(f"Body: {email_data['body']}") # uncomment to view the whole body of an email
                    preview_body = email_data['body'].replace('\n', ' ').replace('\r', '')[:100]
                    logging.info(f"Body preview: {preview_body}")

                    logging.info(f"Attachments: {email_data['attachments']}")
                    logging.info("-" * 40) # Visual separator

                    # client.mark_as_read(email_id)
                
                except Exception as e:
                    logging.error(f"Failed to process email {email_id}: {e}")

    except IMAPClientError as e:
        logging.error(f"IMAP pipeline failed: {e}")
    except Exception as e:
        logging.exception("Unexpected error occurred")

    logging.info("Email ingestion pipeline finished")


if __name__ == "__main__":
    main()
