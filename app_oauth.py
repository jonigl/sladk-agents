import logging
import os
import asyncio

from slack_bolt import App, BoltResponse
from slack_bolt.oauth.callback_options import CallbackOptions, FailureArgs, SuccessArgs
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from listeners import register_listeners
from ai.llm_caller import mcp_toolsets
from ai.mcp_config_loader import close_mcp_toolsets

# Set up logging
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())


# Callback to run on successful installation
def success(args: SuccessArgs) -> BoltResponse:
    # Call default handler to return an HTTP response
    return args.default.success(args)
    # return BoltResponse(status=200, body="Installation successful!")


# Callback to run on failed installation
def failure(args: FailureArgs) -> BoltResponse:
    return args.default.failure(args)
    # return BoltResponse(status=args.suggested_status_code, body=args.reason)


# Initialization
app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    installation_store=FileInstallationStore(),
    oauth_settings=OAuthSettings(
        client_id=os.environ.get("SLACK_CLIENT_ID"),
        client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
        scopes=[
            "assistant:write",
            "im:history",
            "chat:write",
            "files:read",
            "channels:join",  # required only for the channel summary
            "channels:history",  # required only for the channel summary
            "groups:history",  # required only for the channel summary
        ],
        user_scopes=[],
        redirect_uri=None,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        state_store=FileOAuthStateStore(expiration_seconds=600),
        callback_options=CallbackOptions(success=success, failure=failure),
    ),
)

# Register Listeners
register_listeners(app)

# Start Bolt app
if __name__ == "__main__":
    try:
        app.start(3000)
    finally:
        asyncio.run(close_mcp_toolsets(mcp_toolsets))
