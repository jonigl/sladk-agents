from slack_bolt.async_app import AsyncApp

from .app_mentioned import app_mentioned_callback


def register(app: AsyncApp):
    app.event("app_mention")(app_mentioned_callback)
