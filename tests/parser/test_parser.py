import pytest
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from parser import EmailParser

# Initialize handlers
parser = EmailParser()

@pytest.fixture
def attachment_factory():
    def _create(filename, content_type, data):
        main_type, sub_type = content_type.split("/", 1)
        part = MIMEBase(main_type, sub_type)
        part.set_payload(data)
        encoders.encode_base64(part)

        if filename:
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"'
            )
        else:
            part.add_header("Content-Disposition", "attachment")

        return part

    return _create

def test_simple_text_email():
    msg = MIMEText("Just a simple message.")
    msg["Subject"] = "Hello"
    msg["From"] = "friend@test.com"

    result = parser.parse_email(msg.as_bytes())

    assert result["subject"] == "Hello"
    assert result["sender"] == "friend@test.com"
    assert result["body"] == "Just a simple message."
    assert result["attachments"] == []


def test_single_attachment(attachment_factory):
    msg = MIMEMultipart()
    msg["Subject"] = "Invoice"
    msg.attach(MIMEText("Please find attached."))

    msg.attach(
        attachment_factory(
            "invoice.pdf",
            "application/pdf",
            b"%PDF-fake-content",
        )
    )

    result = parser.parse_email(msg.as_bytes())

    assert result["attachments"] == ["invoice.pdf"]


def test_multiple_attachments(attachment_factory):
    msg = MIMEMultipart()
    msg["Subject"] = "Project Files"
    msg.attach(MIMEText("Here are the designs."))

    msg.attach(
        attachment_factory("specs.pdf", "application/pdf", b"x")
    )
    msg.attach(
        attachment_factory("logo.png", "image/png", b"x")
    )

    result = parser.parse_email(msg.as_bytes())

    assert set(result["attachments"]) == {"specs.pdf", "logo.png"}


def test_attachment_missing_filename(attachment_factory):
    msg = MIMEMultipart()
    msg["Subject"] = "Weird Attachment"
    msg.attach(MIMEText("See attached"))

    msg.attach(
        attachment_factory(
            None,
            "application/octet-stream",
            b"mystery-data",
        )
    )

    result = parser.parse_email(msg.as_bytes())

    # Should not crash and should ignore nameless attachment
    assert isinstance(result["attachments"], list)
    assert result["attachments"] == []


def test_html_only_email():
    msg = MIMEText("<p>Hello <b>world</b></p>", "html")
    msg["Subject"] = "HTML only"

    result = parser.parse_email(msg.as_bytes())

    assert "Hello" in result["body"]


@pytest.mark.parametrize(
    "subject, sender",
    [
        ("Normal Subject", "user@test.com"),
        ("こんにちは", "名前 <jp@test.com>"),
        ("=?utf-8?b?SGVsbG8=?=", "encoded@test.com"),
    ],
)
def test_header_decoding(subject, sender):
    msg = MIMEText("Body")
    msg["Subject"] = subject
    msg["From"] = sender

    result = parser.parse_email(msg.as_bytes())

    assert isinstance(result["subject"], str)
    assert isinstance(result["sender"], str)
