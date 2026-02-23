from logging import Logger

from slack_bolt.async_app import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

from ..shared import process_and_stream_message


async def app_mentioned_callback(
    client: AsyncWebClient, event: dict, logger: Logger, say: AsyncSay
):
    """
    Handles the event when the app is mentioned in a Slack conversation
    and generates an AI response.

    Args:
        client: Slack WebClient for making API calls
        event: Event payload containing mention details (channel, user, text, etc.)
        logger: Logger instance for error tracking
        say: Function to send messages to the thread from the app
    """
    await process_and_stream_message(
        client=client,
        logger=logger,
        say=say,
        channel_id=event.get("channel"),
        thread_ts=event.get("thread_ts") or event.get("ts"),
        team_id=event.get("team"),
        user_id=event.get("user"),
        text=event.get("text", ""),
        files=event.get("files") or [],
    )
