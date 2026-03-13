import os
from typing import AsyncIterator, Optional, Tuple

from slack_sdk.models.messages.chunk import PlanUpdateChunk, TaskUpdateChunk

# Human-readable descriptions shown in the task bubble while a tool runs.
# Keys match the tool/agent names registered in call_llm.
_TOOL_DESCRIPTIONS: dict[str, str] = {
    "get_weather": "Fetches current weather conditions for a location.",
    "google_search": "Searches the web using Google Search.",
    "SearchAgent": "Runs a web search to find up-to-date information.",
    "CodeAgent": "Executes code to compute or transform data.",
}


def _details_text(description: str | None, args: dict) -> str | None:
    """Build a plain-text details string for TaskUpdateChunk.

    Renders as:
      <description>
      arg_name: value
      ...
    """
    parts = []
    if description:
        parts.append(description)
    for k, v in args.items():
        parts.append(f"{k}: {v}")
    return "\n".join(parts) or None


def _output_text(response: dict) -> str | None:
    """Extract the most meaningful value from a tool response dict as plain text."""
    value = response.get("result") or response.get("output")
    if value is None and response:
        value = response
    return str(value) if value else None


# Internal protocol constants — not exposed as env vars since users
# don't need to tune Slack streaming details independently.
_CHUNK_BUFFER = 500  # SDK buffer_size: flushes when accumulated text >= this
_TRAILER_RESERVE = 200  # chars reserved for the continuation notice
_CONTINUATION_NOTICE = "\n\n[Continuing in next message…]"

# Derives from the same env var that controls LLM output guidance so there
# is a single knob for "how long can a response be".
_MAX_TOTAL_CHARS = int(os.getenv("AGENT_TARGET_OUTPUT_CHARS", "9000"))


def clamp_to_stream_budget(
    text: str,
    current_total_chars: int,
    max_total_chars: int = _MAX_TOTAL_CHARS,
    reserve_chars: int = _TRAILER_RESERVE,
) -> Tuple[str, bool]:
    """Return (clipped_text, overflowed). overflowed=True when text was cut."""
    allowed = max(0, max_total_chars - reserve_chars - current_total_chars)
    return text[:allowed], len(text) > allowed


async def stream_llm_to_slack(
    client,
    channel_id: str,
    team_id: str,
    user_id: str,
    thread_ts: str,
    llm_chunks: AsyncIterator[dict],
    feedback_blocks: Optional[list] = None,
    task_display_mode: str = "timeline",
) -> None:
    """Stream LLM output to Slack, opening a new message when the budget is exhausted.

    Expects ``llm_chunks`` to yield dicts produced by ``call_llm``:
      - ``{"type": "text",       "content": str}``  — streamed as markdown text
      - ``{"type": "tool_start", "name": str, "id": str}`` — renders an in-progress task bubble
      - ``{"type": "tool_done",  "name": str, "id": str}`` — marks the task bubble complete
    """
    streamer = await client.chat_stream(
        channel=channel_id,
        recipient_team_id=team_id,
        recipient_user_id=user_id,
        thread_ts=thread_ts,
        buffer_size=_CHUNK_BUFFER,
        task_display_mode=task_display_mode,
    )
    streamed_chars = 0
    plan_started = False  # emit PlanUpdateChunk before the first tool task

    try:
        async for event in llm_chunks:
            event_type = event.get("type")

            if event_type == "tool_start":
                args = event.get("args", {})
                description = _TOOL_DESCRIPTIONS.get(event["name"])
                details = _details_text(description, args)
                chunks = []
                if not plan_started:
                    chunks.append(PlanUpdateChunk(title="Running agent tools…"))
                    plan_started = True
                chunks.append(
                    TaskUpdateChunk(
                        id=event["id"],
                        title=f"Calling {event['name']}…",
                        status="in_progress",
                        details=details,
                    )
                )
                await streamer.append(chunks=chunks)

            elif event_type == "tool_done":
                response = event.get("response", {})
                output = _output_text(response)
                await streamer.append(
                    chunks=[
                        TaskUpdateChunk(
                            id=event["id"],
                            title=f"{event['name']} complete",
                            status="complete",
                            output=output,
                        )
                    ]
                )

            elif event_type == "text":
                pending = event["content"]
                while pending:
                    bounded, overflow = clamp_to_stream_budget(pending, streamed_chars)
                    # Guard: if the budget allows nothing (allowed==0) but pending is
                    # non-empty, the loop would spin forever because `pending` never
                    # shrinks.  Force at least one character through so progress is
                    # always guaranteed (can occur when max_total_chars <= reserve_chars).
                    if not bounded and overflow:
                        bounded = pending[:1]
                    if bounded:
                        await streamer.append(markdown_text=bounded)
                        streamed_chars += len(bounded)
                        pending = pending[len(bounded) :]
                    if not overflow:
                        break
                    # Budget exhausted — append continuation notice then open a new message.
                    await streamer.append(markdown_text=_CONTINUATION_NOTICE)
                    await streamer.stop()
                    streamer = await client.chat_stream(
                        channel=channel_id,
                        recipient_team_id=team_id,
                        recipient_user_id=user_id,
                        thread_ts=thread_ts,
                        buffer_size=_CHUNK_BUFFER,
                        task_display_mode=task_display_mode,
                    )
                    streamed_chars = 0

    except Exception:
        try:
            await streamer.stop()
        except Exception:
            pass
        raise

    await streamer.stop(blocks=feedback_blocks)
