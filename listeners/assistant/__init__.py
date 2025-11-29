from slack_bolt.async_app import AsyncApp, AsyncAssistant

from .assistant_thread_started import assistant_thread_started
from .message import message


# Refer to https://docs.slack.dev/tools/bolt-python/concepts/ai-apps#assistant for more details on the Assistant class
def register(app: AsyncApp):
    assistant = AsyncAssistant()

    assistant.thread_started(assistant_thread_started)
    assistant.user_message(message)

    app.assistant(assistant)
