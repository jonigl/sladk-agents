import os
from typing import AsyncIterator, Optional, Tuple

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
    llm_chunks: AsyncIterator[str],
    feedback_blocks: Optional[list] = None,
) -> None:
    """Stream LLM output to Slack, opening a new message when the budget is exhausted."""
    streamer = await client.chat_stream(
        channel=channel_id,
        recipient_team_id=team_id,
        recipient_user_id=user_id,
        thread_ts=thread_ts,
        buffer_size=_CHUNK_BUFFER,
    )
    streamed_chars = 0

    try:
        async for text_chunk in llm_chunks:
            pending = text_chunk
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
                )
                streamed_chars = 0
    except Exception:
        try:
            await streamer.stop()
        except Exception:
            pass
        raise

    await streamer.stop(blocks=feedback_blocks)
