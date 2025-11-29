import os
from typing import Dict, List, AsyncIterator
from google.adk.apps import App
from google.adk.apps.app import EventsCompactionConfig
from google.adk.sessions import InMemorySessionService
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.genai.types import Content, GenerateContentConfig, SafetySetting, HarmCategory, HarmBlockThreshold, Part


APP_NAME = os.getenv("AGENT_APP_NAME", "Sladk_App")
AGENT_NAME = os.getenv("AGENT_NAME", "Sladk_AI_Agent")
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash-preview-09-2025")
DEFAULT_SYSTEM_INSTRUCTION = os.getenv(
    "DEFAULT_SYSTEM_INSTRUCTION",
    """You're an assistant in a Slack workspace.
Users in the workspace will ask you to help them write something or to think better about a specific topic.
You'll respond to those questions in a professional way.
When you include markdown text, convert them to Slack compatible ones.
When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response.""",
)


# Global services
session_service = InMemorySessionService()


async def call_llm(
    messages_in_thread: List[Dict[str, str]],
    system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
    user_id: str = "default_user",
    session_id: str = None,
) -> AsyncIterator[str]:
    """Call the LLM and yield text chunks asynchronously."""

    agent = LlmAgent(
        model=AGENT_MODEL,
        name=AGENT_NAME,
        instruction=system_instruction,
        generate_content_config=GenerateContentConfig(
            temperature=0.2,
            safety_settings=[
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                )
            ],
        ),
    )

    app = App(
        name=APP_NAME,
        root_agent=agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=5,
            overlap_size=1,
        ),
    )

    # Get or create session
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    if not session:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
            state={},
        )

    runner = Runner(
        app=app,
        session_service=session_service,
    )

    latest_user_message = messages_in_thread[-1] if messages_in_thread else None
    if not latest_user_message:
        return

    msg = Content(role="user", parts=[Part(text=latest_user_message["content"])])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=msg,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    yield part.text
        if event.is_final_response():
            break
