import pytest
from unittest.mock import MagicMock, patch
from imap import IMAPClient, IMAPClientError
import imaplib


@pytest.fixture
def env_vars(monkeypatch):
    monkeypatch.setenv("IMAP_SERVER", "imap.test.com")
    monkeypatch.setenv("IMAP_PORT", "993")
    monkeypatch.setenv("EMAIL_ADDRESS", "test@test.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "password")



def test_init_missing_config(monkeypatch):
    monkeypatch.delenv("IMAP_SERVER", raising=False)

    with pytest.raises(IMAPClientError):
        IMAPClient()


def test_init_ok(env_vars):
    client = IMAPClient()
    assert client.server == "imap.test.com"
    assert client.port == 993



@patch("imaplib.IMAP4_SSL")
def test_connect_success(mock_imap, env_vars):
    mock_conn = MagicMock()
    mock_imap.return_value = mock_conn

    client = IMAPClient()
    client.connect()

    mock_imap.assert_called_once()
    mock_conn.login.assert_called_once_with("test@test.com", "password")
    assert client.conn == mock_conn


@patch("imaplib.IMAP4_SSL")
def test_connect_fail(mock_imap, env_vars):
    mock_conn = MagicMock()
    mock_conn.login.side_effect = imaplib.IMAP4.error("auth failed")
    mock_imap.return_value = mock_conn

    client = IMAPClient()

    with pytest.raises(IMAPClientError):
        client.connect()


def test_select_mailbox_ok(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()
    client.conn.select.return_value = ("OK", [])

    client.select_mailbox("INBOX")
    client.conn.select.assert_called_once_with("INBOX")


def test_select_mailbox_fail(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()
    client.conn.select.return_value = ("NO", [])

    with pytest.raises(IMAPClientError):
        client.select_mailbox("INBOX")



def test_search_ok(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()
    client.conn.search.return_value = ("OK", [b"1 2 3"])

    result = client.search("ALL")
    assert result == [b"1", b"2", b"3"]


def test_search_fail(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()
    client.conn.search.return_value = ("NO", [])

    with pytest.raises(IMAPClientError):
        client.search()



def test_fetch_email_ok(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()
    client.conn.fetch.return_value = ("OK", [(None, b"RAW EMAIL")])

    raw = client.fetch_email(b"1")
    assert raw == b"RAW EMAIL"


def test_fetch_email_fail_status(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()
    client.conn.fetch.return_value = ("NO", [])

    with pytest.raises(IMAPClientError):
        client.fetch_email(b"1")


def test_fetch_email_reconnect(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()

    # first call: abort error
    client.conn.fetch.side_effect = [imaplib.IMAP4.abort(), ("OK", [(None, b"RAW")])]

    client._reconnect = MagicMock()

    raw = client.fetch_email(b"1")

    client._reconnect.assert_called_once()
    assert raw == b"RAW"



def test_mark_as_read(env_vars):
    client = IMAPClient()
    client.conn = MagicMock()

    client.mark_as_read(b"1")

    client.conn.store.assert_called_once_with(b"1", "+FLAGS", "\\Seen")



def test_ensure_connection_fail(env_vars):
    client = IMAPClient()
    client.conn = None

    with pytest.raises(IMAPClientError):
        client._ensure_connection()
