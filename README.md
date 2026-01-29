# Email Sorting System

Automated email classification and analysis system that connects to IMAP, classifies emails, saves attachments, and generates reports.

## Features

- **IMAP Connection** - Secure email retrieval with error handling
- **Email Parsing** - Extracts sender, subject, content, and attachments
- **Classification** - Rule-based categorization into 8 categories
- **Attachment Management** - Saves attachments to categorized folders
- **Reporting** - Generates weekly CSV reports with statistics

## Quick Start

1. **Install dependencies in a virtual enviroment:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure email credentials in `.env`:**
   ```env
   IMAP_SERVER=imap.gmail.com
   IMAP_PORT=993
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

3. **Run the application:**
   ```bash
   python src/main.py
   ```

4. **CLI Usage and flags:**
   You can customize the ingestion process using the following flags:
   | Flag | Long Name   | Description                                             | Default  |               
   |-----:|-------------|---------------------------------------------------------|----------|
   | `-m` | `--mailbox` | The IMAP folder to scan (e.g., INBOX, Junk, Archive).   | `INBOX`  |
   | `-s` | `--status`  | Email filter: UNSEEN, SEEN, ALL, FLAGGED, DELETED.      | `UNSEEN` |
   | `-l` | `--limit`   | Maximum number of emails to process in the current run. | `None`   |

5. **Run tests:**
   ```bash
   pytest
   ```

## Project Structure

```
Email_sorting/
├── src/
│   ├── main.py               # Main entry point
│   ├── imap/
│   │   └── client.py         # IMAP connection handler
│   ├── parser/
│   │   ├── email_parser.py   # Email parsing
│   │   └── classification.py # Classification rules
│   ├── reporting/
│   │   ├── attachment.py     # Attachment handler
│   │   ├── reporting.py      # Report generator
│   │   └── database.py       # sql database
│   └── utils/
│       └── logger.py         # Logging setup
├── tests/                    # Test suite
├── output/                   # Generated files
│   ├── attachments/          # Saved attachments by category
│   ├── reports/              # CSV reports
│   └── email.db              # Database      
└── requirements.txt          # Dependencies
```



## Categories

The system classifies emails into:
- Security, Finance, Marketing, Job Market, Tech, Meetings, Travel, Social, Internal, General

## Output

- **Attachments:** `output/attachments/{category}/filename.ext`
- **Reports:** `output/reports/email_report_YYYY-WWW.csv` and `summary_report_YYYY-WWW.csv`

## Requirements

- Python 3.8+
- IMAP-enabled email account
- See `requirements.txt` for Python packages
