from logging import Logger
from typing import Dict, List

from slack_bolt.async_app import AsyncBoltContext, AsyncSay, AsyncSetStatus
from slack_sdk.web.async_client import AsyncWebClient

from ai.llm_caller import call_llm

from ..views.feedback_block import create_feedback_block


async def message(
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
    payload: dict,
    say: AsyncSay,
    set_status: AsyncSetStatus,
):
    """
    Handles when users send messages or select a prompt in an assistant thread and generate AI responses:

    Args:
        client: Slack WebClient for making API calls
        context: Bolt context containing channel and thread information
        logger: Logger instance for error tracking
        payload: Event payload with message details (channel, user, text, etc.)
        say: Function to send messages to the thread
        set_status: Function to update the assistant's status
    """
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id

        await set_status(
            status="thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        replies = await client.conversations_replies(
            channel=context.channel_id,
            ts=context.thread_ts,
            oldest=context.thread_ts,
            limit=10,
        )
        messages_in_thread: List[Dict[str, str]] = []
        for msg in replies["messages"]:
            role = "user" if msg.get("bot_id") is None else "assistant"
            messages_in_thread.append({"role": role, "content": msg["text"]})

        streamer = await client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
        )

        # Loop over streaming response from LLM
        async for text_chunk in call_llm(
            messages_in_thread,
            user_id=user_id,
            session_id=thread_ts
        ):
            await streamer.append(markdown_text=text_chunk)

        feedback_block = create_feedback_block()
        await streamer.stop(blocks=feedback_block)

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        await say(f":warning: Something went wrong! ({e})")
