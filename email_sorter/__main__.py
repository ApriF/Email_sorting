import argparse
import sys
import logging

from utils import setup_logger
from imap import IMAPClient, IMAPClientError
from parser import EmailParser, EmailClassifier
from reporting import AttachmentHandler, ReportGenerator, EmailDatabase

def run_pipeline(mailbox="INBOX", status="UNSEEN", limit=None, domain=None):
    """
    Core ingestion logic.
    :param mailbox: The IMAP folder to scan
    :param status: The search criteria (UNSEEN, SEEN, ALL, etc.)
    :param limit: Maximum number of emails to process
    """
    setup_logger()
    logging.info("Starting email ingestion pipeline [Mailbox: {mailbox}] [Status: {status}]")

    # Initialize handlers
    parser = EmailParser()
    classifier = EmailClassifier()
    attachment_handler = AttachmentHandler()
    report_generator = ReportGenerator()
    database = EmailDatabase()

    if domain:
        classifier.internal_domain = domain.lower()

    try:
        with IMAPClient() as client:
            client.select_mailbox(mailbox)

            email_ids = client.search(status)
            if not email_ids:
                logging.info(f"No emails found matching criteria: {status}")
                return

            if limit:
                email_ids = email_ids[:limit]
            
            logging.info(f"{len(email_ids)} emails with status: {status} found to process")

            for email_id in email_ids:
                raw_email = None
                try:
                    raw_email = client.fetch_email(email_id)
                    logging.info(f"Email {email_id.decode()} fetched")

                    # Parse email
                    email_data = parser.parse_email(raw_email)
                    
                    # Classify email
                    email_category = classifier.classify_email(email_data)

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
                    if status.upper() == "UNSEEN":
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
        ("Detail", "Summary"),
        report_generator.generate_reports(),
    ):
        if path:
            logging.info(f"{name} report saved: {path}")

    # Close database connection
    database.close()
    logging.info("Email ingestion pipeline finished")

def main():
    arg_parser = argparse.ArgumentParser(
        description="Ingest, classify, and report on emails from an IMAP server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    arg_parser.add_argument(
        "-m", "--mailbox", 
        default="INBOX", 
        help="The IMAP mailbox to check"
    )
    
    arg_parser.add_argument(
        "-s", "--status", 
        default="UNSEEN", 
        choices=["UNSEEN", "SEEN", "ALL", "FLAGGED", "DELETED"],
        help="Search criteria for emails"
    )
    
    arg_parser.add_argument(
        "-l", "--limit", 
        type=int, 
        help="Maximum number of emails to process"
    )

    arg_parser.add_argument(
        "-d", "--domain", 
        help="Override the internal domain (e.g., @custom.com)"
    )
    
    args = arg_parser.parse_args()

    try:
        run_pipeline(
            mailbox=args.mailbox, 
            status=args.status, 
            limit=args.limit,
            domain=args.domain
        )
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
