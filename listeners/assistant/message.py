from logging import Logger

from slack_bolt.async_app import AsyncBoltContext, AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from ..shared import process_and_stream_message


async def message(
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
    payload: dict,
    say: AsyncSay,
):
    """
    Handles when users send messages or select a prompt in an assistant thread and generate AI responses:

    Args:
        client: Slack WebClient for making API calls
        context: Bolt context containing channel and thread information
        logger: Logger instance for error tracking
        payload: Event payload with message details (channel, user, text, etc.)
        say: Function to send messages to the thread
    """
    await process_and_stream_message(
        client=client,
        logger=logger,
        say=say,
        channel_id=payload.get("channel"),
        thread_ts=payload.get("thread_ts"),
        team_id=context.team_id,
        user_id=context.user_id,
        text=payload.get("text", ""),
        files=payload.get("files") or [],
    )
