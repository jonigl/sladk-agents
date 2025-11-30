from logging import Logger
from typing import Dict, List

from slack_bolt.async_app import AsyncSay, AsyncSetSuggestedPrompts


async def assistant_thread_started(
    say: AsyncSay,
    set_suggested_prompts: AsyncSetSuggestedPrompts,
    logger: Logger,
):
    """
    Handle the assistant thread start event by greeting the user and setting suggested prompts.

    Args:
        say: Function to send messages to the thread from the app
        set_suggested_prompts: Function to configure suggested prompt options
        logger: Logger instance for error tracking
    """
    try:
        await say("How can I help you?")

        prompts: List[Dict[str, str]] = [
            {
                "title": "What does Slack stand for?",
                "message": "Slack, a business communication service, was named after an acronym. Can you guess what it stands for?",
            },
            {
                "title": "What Google ADK is?",
                "message": "Google Agents Development Kit (ADK) is a framework for building AI agents that can interact with various Google services. Can you explain how Google ADK works and its main features?",
            },
            {
                "title": "What Sladk Agents is? ",
                "message": "Sladk Agents is a project that integrates Slack AI Agents with Google Agents Development Kit (ADK). What could be the benefits of using Sladk Agents in a workspace?",
            },
        ]

        await set_suggested_prompts(prompts=prompts)
    except Exception as e:
        logger.exception(f"Failed to handle an assistant_thread_started event: {e}")
        await say(f":warning: Something went wrong! ({e})")
