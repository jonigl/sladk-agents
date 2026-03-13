from logging import Logger
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

        await set_suggested_prompts(
            prompts=[
                {
                    "title": "Check the weather in Tokyo and Miami (plan view)",
                    "message": "What's the weather like in Tokyo and Miami right now?",
                },
                {
                    "title": "Latest news about AI (timeline view)",
                    "message": "Search for latest news about AI.",
                },
                {
                    "title": "What Sladk Agents is? ",
                    "message": "Sladk Agents is a project that integrates Slack AI Agents with Google Agents Development Kit (ADK). What could be the benefits of using Sladk Agents in a workspace?",
                },
            ]
        )
    except Exception as e:
        logger.exception(f"Failed to handle an assistant_thread_started event: {e}")
        await say(f":warning: Something went wrong! ({e})")
