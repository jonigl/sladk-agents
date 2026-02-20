import logging
import os
from typing import Dict, List, AsyncIterator
from google.adk.agents import Agent, LlmAgent
from google.adk.apps import App
from google.adk.apps.app import EventsCompactionConfig
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import (
    Content,
    GenerateContentConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
    Part,
)
from ai.tools.custom_tools import get_weather
from ai.utils import load_system_instruction

logger = logging.getLogger(__name__)

APP_NAME = os.getenv("AGENT_APP_NAME", "Sladk_App")
AGENT_NAME = os.getenv("AGENT_NAME", "Sladk_AI_Agent")
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")

DEFAULT_SYSTEM_INSTRUCTION = load_system_instruction()


# Global services
session_service = InMemorySessionService()


async def call_llm(
    messages_in_thread: List[Dict[str, str]],
    system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
    user_id: str = "default_user",
    session_id: str = None,
) -> AsyncIterator[str]:
    """Call the LLM and yield text chunks asynchronously."""
    search_agent = Agent(
        model=AGENT_MODEL,
        name="SearchAgent",
        instruction="You're a specialist in Google Search",
        tools=[google_search],
    )

    coding_agent = Agent(
        model=AGENT_MODEL,
        name="CodeAgent",
        instruction="You're a specialist in Code Execution",
        code_executor=BuiltInCodeExecutor(),
    )

    agent = LlmAgent(
        model=AGENT_MODEL,
        name=AGENT_NAME,
        instruction=system_instruction,
        generate_content_config=GenerateContentConfig(
            temperature=0.4,
            safety_settings=[
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                )
            ],
        ),
        tools=[
            get_weather,
            AgentTool(agent=search_agent),
            AgentTool(agent=coding_agent),
        ],
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
