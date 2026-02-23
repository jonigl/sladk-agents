import asyncio
import io
import logging
import os
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import aiohttp
from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_CHARS = int(os.getenv("ATTACHMENT_MAX_CHAR_BUDGET", "200000"))
MAX_FILES_PER_MESSAGE = int(os.getenv("ATTACHMENT_MAX_FILES", "5"))
DOWNLOAD_TIMEOUT_SECONDS = int(os.getenv("ATTACHMENT_DOWNLOAD_TIMEOUT", "15"))


def classify_file(file_info: Dict[str, Any]) -> Optional[str]:
    mode = (file_info.get("mode") or "").lower()
    mimetype = (file_info.get("mimetype") or "").lower()
    filetype = (file_info.get("filetype") or "").lower()
    name = (file_info.get("name") or file_info.get("title") or "").lower()

    if mode in {"snippet", "post"}:
        return "snippet"
    if mimetype == "application/pdf" or filetype == "pdf" or name.endswith(".pdf"):
        return "pdf"
    if (
        mimetype.startswith("text/")
        or filetype in {"txt", "text"}
        or name.endswith(".txt")
    ):
        return "text"
    return None


async def download_slack_file_bytes(url: str, slack_token: str) -> bytes:
    timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)
    headers = {"Authorization": f"Bearer {slack_token}"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.read()


def extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _decode_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip()


def enrich_text_with_attachments(
    text: str,
    attachment_context: str,
    warnings: List[str],
) -> str:
    """Append attachment content and ingestion warnings to a user message."""
    enriched = text
    if attachment_context:
        enriched = (
            f"{enriched}\n\n"
            "Attached file content from the same message:\n"
            f"{attachment_context}"
        )
    if warnings:
        warning_block = "\n".join(f"- {w}" for w in warnings)
        enriched = (
            f"{enriched}\n\n"
            "Attachment ingestion notes (mention these briefly to the user):\n"
            f"{warning_block}"
        )
    return enriched


async def _process_single_attachment(
    file_info: Dict[str, Any],
    slack_token: str,
    downloader: Callable[[str, str], Awaitable[bytes]],
    remaining_budget: int,
) -> Tuple[Optional[str], Optional[str], int]:
    """Process a single file attachment and return (parsed_section, warning, consumed_budget)."""
    file_kind = classify_file(file_info)
    filename = file_info.get("name") or file_info.get("title") or "unnamed-file"

    if not file_kind:
        return None, None, 0

    url = file_info.get("url_private_download") or file_info.get("url_private")
    if not url:
        return None, f"Skipped {filename}: no downloadable URL in Slack payload.", 0

    try:
        payload = await downloader(url, slack_token)
        extracted = extract_pdf_text(payload) if file_kind == "pdf" else _decode_text(payload)

        if not extracted:
            return None, f"Skipped {filename}: no readable text content found.", 0

        truncated = extracted[:remaining_budget]
        was_truncated = len(truncated) < len(extracted)

        section = [f"[Attachment: {filename} | type={file_kind}]", truncated]
        if was_truncated:
            section.append("[Attachment content truncated due to context budget]")
        section.append("[/Attachment]")

        return "\n".join(section), None, len(truncated)

    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
        PdfReadError,
        UnicodeDecodeError,
        ValueError,
        RuntimeError,
        OSError,
    ) as exc:
        logger.exception("Attachment ingestion failed for %s: %s", filename, exc)
        return None, f"Could not read {filename}: {exc}", 0


async def ingest_latest_message_attachments(
    files: List[Dict[str, Any]],
    slack_token: Optional[str],
    downloader: Optional[Callable[[str, str], Awaitable[bytes]]] = None,
) -> Tuple[str, List[str]]:
    if not files:
        return "", []

    if not slack_token:
        return "", ["Could not read attachments: missing Slack bot token."]

    active_downloader = downloader or download_slack_file_bytes
    remaining_budget = MAX_ATTACHMENT_CHARS

    parsed_sections: List[str] = []
    warnings: List[str] = []

    for file_info in files[:MAX_FILES_PER_MESSAGE]:
        if remaining_budget <= 0:
            warnings.append(
                "Attachment content budget reached; skipped remaining files."
            )
            break

        section, warning, consumed = await _process_single_attachment(
            file_info, slack_token, active_downloader, remaining_budget
        )

        if section:
            parsed_sections.append(section)
        if warning:
            warnings.append(warning)

        remaining_budget -= consumed

    if len(files) > MAX_FILES_PER_MESSAGE:
        warnings.append(
            f"Read the first {MAX_FILES_PER_MESSAGE} files only; ignored additional attachments."
        )

    return "\n\n".join(parsed_sections), warnings
