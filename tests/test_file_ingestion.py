import asyncio

from ai.file_ingestion import (
    classify_file,
    enrich_text_with_attachments,
    ingest_latest_message_attachments,
)


def test_classify_supported_files():
    assert classify_file({"mimetype": "text/plain", "name": "note.txt"}) == "text"
    assert classify_file({"mode": "snippet", "name": "code.py"}) == "snippet"
    assert classify_file({"mimetype": "application/pdf", "name": "doc.pdf"}) == "pdf"


def test_classify_unsupported_file():
    assert classify_file({"mimetype": "image/png", "name": "img.png"}) is None


def test_enrich_text_with_no_attachments():
    assert enrich_text_with_attachments("hello", "", []) == "hello"


def test_enrich_text_appends_context_and_warnings():
    result = enrich_text_with_attachments(
        "hello",
        "[Attachment: notes.txt]content[/Attachment]",
        ["Could not read bad.pdf: boom"],
    )
    assert "hello" in result
    assert "Attached file content" in result
    assert "Attachment ingestion notes" in result
    assert "Could not read bad.pdf" in result


def test_ingests_text_and_warns_on_unsupported_and_limit():
    async def fake_downloader(_url: str, _token: str) -> bytes:
        return b"hello from file"

    files = [
        {
            "name": "notes.txt",
            "mimetype": "text/plain",
            "url_private_download": "https://files/1",
        },
        {
            "name": "ignore.png",
            "mimetype": "image/png",
            "url_private_download": "https://files/2",
        },
    ]

    content, warnings = asyncio.run(
        ingest_latest_message_attachments(
            files=files,
            slack_token="xoxb-test",
            downloader=fake_downloader,
        )
    )

    assert "[Attachment: notes.txt" in content
    assert "hello from file" in content
    assert all("ignore.png" not in warning for warning in warnings)


def test_warns_when_token_missing():
    content, warnings = asyncio.run(
        ingest_latest_message_attachments(
            files=[{"name": "notes.txt", "mimetype": "text/plain"}],
            slack_token=None,
        )
    )

    assert content == ""
    assert any("missing Slack bot token" in warning for warning in warnings)


def test_warns_on_download_error():
    async def broken_downloader(_url: str, _token: str) -> bytes:
        raise RuntimeError("boom")

    content, warnings = asyncio.run(
        ingest_latest_message_attachments(
            files=[
                {
                    "name": "notes.txt",
                    "mimetype": "text/plain",
                    "url_private_download": "https://files/1",
                }
            ],
            slack_token="xoxb-test",
            downloader=broken_downloader,
        )
    )

    assert content == ""
    assert any("Could not read notes.txt" in warning for warning in warnings)
