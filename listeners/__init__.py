from slack_bolt.async_app import AsyncApp

from listeners import actions, assistant, events


def register_listeners(app: AsyncApp):
    actions.register(app)
    assistant.register(app)
    events.register(app)
