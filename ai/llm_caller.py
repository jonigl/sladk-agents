import logging
import os
from typing import AsyncIterator
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
from ai.tools.custom_tools import get_weather, get_current_time
from ai.mcp_config_loader import load_mcp_toolsets_from_file
from ai.utils import load_system_instruction

logger = logging.getLogger(__name__)

APP_NAME = os.getenv("AGENT_APP_NAME", "Sladk_App")
AGENT_NAME = os.getenv("AGENT_NAME", "Sladk_AI_Agent")
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
AGENT_MAX_OUTPUT_TOKENS = int(os.getenv("AGENT_MAX_OUTPUT_TOKENS", "0"))
AGENT_TARGET_OUTPUT_CHARS = int(os.getenv("AGENT_TARGET_OUTPUT_CHARS", "9000"))
MCP_CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", "mcpServers.json")

DEFAULT_SYSTEM_INSTRUCTION = load_system_instruction()


# Global services
session_service = InMemorySessionService()
mcp_toolsets = load_mcp_toolsets_from_file(MCP_CONFIG_PATH)


async def call_llm(
    user_prompt: str,
    system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
    user_id: str = "default_user",
    session_id: str = None,
) -> AsyncIterator[dict]:
    """Call the LLM and yield structured event dicts asynchronously.

    Yields dicts with a ``type`` key:
      - ``{"type": "text", "content": str}``
      - ``{"type": "tool_start", "name": str, "id": str}``
      - ``{"type": "tool_done",  "name": str, "id": str}``
    """
    if not user_prompt:
        return

    effective_instruction = (
        f"{system_instruction}\n\n"
        "Response length guidance:\n"
        f"- Keep the default response under ~{AGENT_TARGET_OUTPUT_CHARS} characters.\n"
        "- Prefer concise answers unless the user explicitly asks for deep detail."
    )

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

    generation_config = GenerateContentConfig(
        temperature=0.4,
        safety_settings=[
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ],
    )
    if AGENT_MAX_OUTPUT_TOKENS > 0:
        generation_config.max_output_tokens = AGENT_MAX_OUTPUT_TOKENS

    agent = LlmAgent(
        model=AGENT_MODEL,
        name=AGENT_NAME,
        instruction=effective_instruction,
        generate_content_config=generation_config,
        tools=[
            get_weather,
            get_current_time,
            AgentTool(agent=search_agent),
            AgentTool(agent=coding_agent),
            *mcp_toolsets,
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

    msg = Content(role="user", parts=[Part(text=user_prompt)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=msg,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    yield {
                        "type": "tool_start",
                        "name": fc.name,
                        "id": fc.id or fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }
                elif hasattr(part, "function_response") and part.function_response:
                    fr = part.function_response
                    yield {
                        "type": "tool_done",
                        "name": fr.name,
                        "id": fr.id or fr.name,
                        "response": dict(fr.response) if fr.response else {},
                    }
                elif hasattr(part, "text") and part.text:
                    yield {"type": "text", "content": part.text}
        if event.is_final_response():
            break
