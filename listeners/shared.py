from logging import Logger
from typing import Optional

from slack_bolt.async_app import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from ai.file_ingestion import enrich_text_with_attachments, ingest_latest_message_attachments
from ai.llm_caller import call_llm
from ai.slack_streaming import stream_llm_to_slack
from .views.feedback_block import create_feedback_block


async def process_and_stream_message(
    client: AsyncWebClient,
    logger: Logger,
    say: AsyncSay,
    channel_id: Optional[str],
    thread_ts: Optional[str],
    team_id: Optional[str],
    user_id: Optional[str],
    text: str,
    files: list,
):
    try:
        attachment_context, warnings = await ingest_latest_message_attachments(
            files=files,
            slack_token=getattr(client, "token", None),
        )
        enriched_text = enrich_text_with_attachments(text, attachment_context, warnings)

        await client.assistant_threads_setStatus(
            channel_id=channel_id,
            thread_ts=thread_ts,
            status="thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        await stream_llm_to_slack(
            client=client,
            channel_id=channel_id,
            team_id=team_id,
            user_id=user_id,
            thread_ts=thread_ts,
            llm_chunks=call_llm(enriched_text, user_id=user_id, session_id=thread_ts),
            feedback_blocks=create_feedback_block(),
        )

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        if channel_id and thread_ts:
            await client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=":warning: Something went wrong while generating the response.",
            )
        else:
            await say(":warning: Something went wrong while generating the response.")
