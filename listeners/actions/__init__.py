from slack_bolt.async_app import AsyncApp

from .actions import handle_feedback


def register(app: AsyncApp):
    app.action("feedback")(handle_feedback)
