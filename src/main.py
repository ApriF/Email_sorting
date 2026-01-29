from imap.client import IMAPClient, IMAPClientError
from utils.logger import setup_logger
import logging

import parser.email_parser as parser
import parser.classification as category
from reporting.attachment import AttachmentHandler
from reporting.reporting import ReportGenerator
from reporting.database import EmailDatabase

def main():
    setup_logger()
    logging.info("Starting email ingestion pipeline")

    # Initialize handlers
    attachment_handler = AttachmentHandler()
    report_generator = ReportGenerator()
    database = EmailDatabase()

    try:
        with IMAPClient() as client:
            client.select_mailbox("INBOX")

            email_ids = client.search("UNSEEN")
            logging.info(f"{len(email_ids)} unread emails found")

            for email_id in email_ids:
                try:
                    raw_email = client.fetch_email(email_id)
                    logging.info(f"Email {email_id.decode()} fetched")

                    # Parse email
                    email_data = parser.parse_email(raw_email)
                    
                    # Classify email
                    email_category = category.classify_email(email_data)

                    # Log email information
                    logging.info(f"Sender: {email_data['sender']}")
                    logging.info(f"Subject: {email_data['subject']}")
                    logging.info(f"Date: {email_data['date']}")
                    logging.info(f"Category: {email_category}")

                    # Body preview
                    preview_body = email_data['body'].replace('\n', ' ').replace('\r', '')[:100]
                    logging.info(f"Body preview: {preview_body}")

                    # Handle attachments
                    has_attachments = len(email_data['attachments']) > 0
                    saved_files = []
                    if has_attachments:
                        logging.info(f"Attachments found: {email_data['attachments']}")
                        saved_files = attachment_handler.save_attachments(
                            raw_email, 
                            email_category, 
                            email_id
                        )
                        if saved_files:
                            logging.info(f"Saved {len(saved_files)} attachment(s)")
                    else:
                        logging.info("No attachments found")

                    # Save to database
                    db_email_id = database.insert_email(
                        email_data,
                        email_category,
                        has_attachments=has_attachments
                    )
                    
                    # Save attachments to database
                    for file_path in saved_files:
                        filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                        database.insert_attachment(db_email_id, filename, file_path, email_category)

                    # Record email for reporting
                    report_generator.record_email(
                        email_data, 
                        email_category, 
                        has_attachments=has_attachments
                    )

                    logging.info("-" * 40)  # Visual separator

                    # Mark email as read after successful processing
                    client.mark_as_read(email_id)
                
                except Exception as e:
                    logging.error(f"Failed to process email {email_id}: {e}", exc_info=True)
                    # Record error in database and report
                    try:
                        email_data = parser.parse_email(raw_email)
                        database.insert_email(email_data, "ERROR", error=str(e))
                        report_generator.record_email(
                            email_data, 
                            "ERROR", 
                            error=str(e)
                        )
                    except:
                        # If parsing also fails, record minimal info
                        error_data = {'sender': '', 'subject': '', 'date': '', 'attachments': []}
                        database.insert_email(error_data, "ERROR", error=str(e))
                        report_generator.record_email(
                            error_data, 
                            "ERROR", 
                            error=str(e)
                        )

    except IMAPClientError as e:
        logging.error(f"IMAP pipeline failed: {e}")
    except Exception as e:
        logging.exception("Unexpected error occurred")

    logging.info("Generating reports...")
    for name, path in zip(
        ("Weekly", "Summary", "Repartition"),
        report_generator.generate_reports(),
    ):
        if path:
            logging.info(f"{name} report saved: {path}")

    # Close database connection
    database.close()
    logging.info("Email ingestion pipeline finished")


if __name__ == "__main__":
    main()
