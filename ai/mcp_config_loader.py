import json
import logging
import os
import re
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from mcp import StdioServerParameters

from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

logger = logging.getLogger(__name__)
_ENV_PATTERN = re.compile(r"\$\{env:([^}]+)\}")


def _expand_string(value: str) -> str:
    expanded = _ENV_PATTERN.sub(lambda m: os.getenv(m.group(1), ""), value)
    return expanded.replace("${workspaceFolder}", os.getcwd())


def expand_config_values(value: Any) -> Any:
    """Recursively expand supported placeholders in config values."""
    if isinstance(value, str):
        return _expand_string(value)
    if isinstance(value, list):
        return [expand_config_values(item) for item in value]
    if isinstance(value, dict):
        return {k: expand_config_values(v) for k, v in value.items()}
    return value


def create_toolset_from_config(name: str, config: Dict[str, Any]) -> McpToolset:
    """Create one MCP toolset from a single server config object."""
    expanded = expand_config_values(config)

    if "command" in expanded:
        command = expanded["command"]
        if not isinstance(command, str) or not command.strip():
            raise ValueError("'command' must be a non-empty string")

        args = expanded.get("args", [])
        if not isinstance(args, list):
            raise ValueError("'args' must be a list when provided")

        env = expanded.get("env", {})
        if env is None:
            env = {}
        if not isinstance(env, dict):
            raise ValueError("'env' must be an object when provided")

        connection_params = StdioConnectionParams(
            server_params=StdioServerParameters(
                command=command,
                args=args,
                env={**os.environ, **env},
            ),
            timeout=30,
        )
    elif "url" in expanded:
        url = expanded["url"]
        if not isinstance(url, str) or not url.strip():
            raise ValueError("'url' must be a non-empty string")

        headers = expanded.get("headers", {})
        if headers is None:
            headers = {}
        if not isinstance(headers, dict):
            raise ValueError("'headers' must be an object when provided")

        if url.rstrip("/").lower().endswith("/sse"):
            connection_params = SseConnectionParams(
                url=url,
                headers=headers,
            )
        else:
            connection_params = StreamableHTTPConnectionParams(
                url=url,
                headers=headers,
            )
    else:
        raise ValueError("Config must include either 'command' or 'url'")

    tool_filter = expanded.get("tool_filter")
    if tool_filter is not None and not isinstance(tool_filter, list):
        raise ValueError("'tool_filter' must be a list when provided")

    toolset = McpToolset(
        connection_params=connection_params,
        tool_filter=tool_filter,
    )
    logger.debug("Created MCP toolset for server '%s'", name)
    return toolset


def load_mcp_toolsets_from_file(config_path: str) -> List[McpToolset]:
    """Load MCP toolsets from a JSON configuration file.

    Returns only successfully-created toolsets; per-server failures are logged
    and skipped so one bad entry does not stop the app.
    """
    path = Path(config_path)
    if not path.exists():
        logger.info("MCP config file not found at %s; skipping MCP toolsets", path)
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse MCP config '%s': %s", path, exc)
        return []
    except OSError as exc:
        logger.error("Failed to read MCP config '%s': %s", path, exc)
        return []

    servers = payload.get("mcpServers", {})
    if not isinstance(servers, dict):
        logger.error("Invalid MCP config '%s': 'mcpServers' must be an object", path)
        return []

    toolsets: List[McpToolset] = []
    for name, config in servers.items():
        if not isinstance(config, dict):
            logger.error(
                "[FAIL] Failed to load MCP server '%s': config must be an object", name
            )
            continue
        try:
            toolsets.append(create_toolset_from_config(name=name, config=config))
            logger.info("[OK] Loaded MCP server: %s", name)
        except Exception as exc:
            logger.error("[FAIL] Failed to load MCP server '%s': %s", name, exc)

    return toolsets


async def close_mcp_toolsets(toolsets: List[McpToolset]) -> None:
    """Close all MCP toolsets, logging and continuing on individual failures."""
    for toolset in toolsets:
        try:
            await toolset.close()
        except Exception as exc:
            logger.warning("Failed closing MCP toolset: %s", exc)
