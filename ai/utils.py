import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_FALLBACK_SYSTEM_INSTRUCTION = """You're an assistant in a Slack workspace.
Users in the workspace will ask you to help them write something or to think better about a specific topic.
You'll respond to those questions in a professional way.
When you include markdown text, convert them to Slack compatible ones.
When a prompt has Slack's special syntax like <@USER_ID> or <#CHANNEL_ID>, you must keep them as-is in your response."""


def load_system_instruction() -> str:
    """Resolve the system instruction using this priority order:
    1. DEFAULT_SYSTEM_INSTRUCTION env var (highest priority)
    2. AGENTS.md file (path from AGENTS_MD_PATH env var, default: ./AGENTS.md)
    3. Hardcoded Slack-assistant default (fallback)
    """
    # 1. Env var wins
    env_instruction = os.getenv("DEFAULT_SYSTEM_INSTRUCTION")
    if env_instruction:
        logger.info(
            "System instruction loaded from DEFAULT_SYSTEM_INSTRUCTION env var."
        )
        return env_instruction

    # 2. AGENTS.md file
    agents_md_path = Path(os.getenv("AGENTS_MD_PATH", "AGENTS.md"))
    try:
        content = agents_md_path.read_text(encoding="utf-8").strip()
        if content:
            logger.info(
                "System instruction loaded from file: %s", agents_md_path.resolve()
            )
            return content
        else:
            logger.warning(
                "File %s is empty, falling back to default.", agents_md_path.resolve()
            )
    except FileNotFoundError:
        logger.debug(
            "No AGENTS.md found at %s, using built-in default.",
            agents_md_path.resolve(),
        )
    except (OSError, UnicodeDecodeError) as e:
        logger.warning(
            "Could not read %s (%s), falling back to built-in default.",
            agents_md_path.resolve(),
            e,
        )

    # 3. Fallback default
    logger.info("System instruction: using built-in Slack assistant default.")
    return _FALLBACK_SYSTEM_INSTRUCTION
