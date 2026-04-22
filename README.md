# sladk-agents

**sladk-agents** helps you run AI agents in your Slack workspace. It is powered by [Google ADK](https://google.github.io/adk-docs/) and [Bolt for Python](https://docs.slack.dev/tools/bolt-python). Multi-agent assistant in the side panel, threads, @mentions, and DMs, with streaming and tools.

[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Gemini-orange)](https://ai.google.dev/)
[![Google ADK](https://img.shields.io/badge/Google-ADK-green)](https://google.github.io/adk-docs/)
[![Slack Bolt](https://img.shields.io/badge/Slack-Bolt%20for%20Python-purple)](https://docs.slack.dev/tools/bolt-python)

## What it does

- **Slack-native** - Uses Slack’s [AI Agent](https://docs.slack.dev/ai/) surfaces (side panel, threads, @mentions, DMs).
- **Google ADK** - Root agent (Gemini) + sub-agents (e.g. search, code execution) and custom tools.
- **Sessions** - Conversation state per thread; configurable context compaction.
- **Streaming** - Responses streamed in real time.

## Quick start

**Prerequisites:** [uv](https://docs.astral.sh/uv/getting-started/installation/), Slack workspace (admin), [Google API key](https://aistudio.google.com/app/api-keys) with Gemini.

```bash
git clone https://github.com/jonigl/sladk-agents.git
cd sladk-agents
cp .env.sample .env
# Edit .env: SLACK_APP_TOKEN, SLACK_BOT_TOKEN, GOOGLE_API_KEY, AGENT_MODEL (e.g. gemini-2.5-flash)
cp AGENTS.md.sample AGENTS.md
# Edit AGENTS.md to define your agent's persona (optional — a default is used if omitted)
uv sync
```

> `uv` manages the virtual environment and dependencies automatically — no manual `venv` or `pip install` needed.

**Slack app:** [Create an app](https://api.slack.com/apps/new) from manifest → paste `manifest.json` → Install to workspace. See [SLACK_BOLT_TEMPLATE_README.md](SLACK_BOLT_TEMPLATE_README.md#creating-the-slack-app) if you need step-by-step.

**Run:**

```bash
uv run python app.py
```

Or using Slack CLI:

```bash
slack run
```

## Output length controls

Two `.env` knobs control response length:

- `AGENT_MAX_OUTPUT_TOKENS` — hard cap on ADK/Gemini output tokens; set `0` to disable (default `0`)
- `AGENT_TARGET_OUTPUT_CHARS` — character budget applied both to the concise-response guidance sent to the LLM and to each Slack streaming message (default `9000`)

When a response exceeds the streaming budget, the app continues automatically in the same thread with a follow-up message.

**Attachment handling** (optional overrides): `ATTACHMENT_MAX_CHAR_BUDGET` (default `200000`), `ATTACHMENT_MAX_FILES` (default `5`), `ATTACHMENT_DOWNLOAD_TIMEOUT` (default `15` seconds).

Slack: **Preferences → Navigation → App agents & assistants** → enable **Show app agents**. Then use the agent via the side panel, @mention in a channel, or DM.

## Usage

| Where        | How |
|-------------|-----|
| Side panel  | Agent icon (top right) in Slack |
| Channel     | `@YourBotName` in a message |
| DM          | Direct message to the bot |

Example prompts: search the web, run Python snippets, or use built-in tools like weather (see `ai/tools/custom_tools.py`).

## Agent persona (AGENTS.md)

You can give the agent a completely different role or personality without touching any code — just drop an `AGENTS.md` file in the project root.

```bash
cp AGENTS.md.sample AGENTS.md
# Edit AGENTS.md with any role, e.g. a security & compliance reviewer or a legal assistant
```

The full file content becomes the system instruction sent to the LLM. Restart the app to pick up changes.

**Resolution order** (highest wins):

| Priority | Source | When |
|----------|--------|---------|
| 1 | `DEFAULT_SYSTEM_INSTRUCTION` env var | Always the highest priority |
| 2 | `AGENTS.md` file | When env var is not set |
| 3 | Built-in Slack assistant default | Fallback when neither is set |

To load the file from a different path, set `AGENTS_MD_PATH` in your `.env`:

```bash
AGENTS_MD_PATH=/path/to/my-agent.md
```

`AGENTS.md` is git-ignored (like `.env`) so each deployment can have its own persona. Commit `AGENTS.md.sample` as a template.

> **Docker / Kubernetes** — either bake `AGENTS.md` into the image or mount it as a volume / ConfigMap and set `AGENTS_MD_PATH` accordingly.

## Extending

Add tools in `ai/tools/custom_tools.py` and register them on the agent in `ai/llm_caller.py`:

```python
# ai/tools/custom_tools.py
def my_tool(param: str) -> str:
    """What the tool does. Args: param. Returns: result."""
    return result

# ai/llm_caller.py — add to tools=[...]
from ai.tools.custom_tools import get_weather, my_tool
tools=[get_weather, my_tool, AgentTool(agent=search_agent), ...]
```

### MCP servers via JSON config

You can add MCP (Model Context Protocol) tools without changing Python code by creating `mcpServers.json` in the project root.

```bash
cp mcpServers.json.sample mcpServers.json
# Edit mcpServers.json with your MCP servers
```

Supported server config shape (`mcpServers` object):

- `command` + optional `args`/`env` -> local stdio MCP server
- `url` ending in `/sse` -> SSE MCP server
- any other `url` (including `/mcp`) -> Streamable HTTP MCP server

Supported placeholders in all string values:

- `${env:VAR_NAME}` -> environment variable value (empty string if unset)
- `${workspaceFolder}` -> current working directory

Example:

```json
{
    "mcpServers": {
        "local-filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "${workspaceFolder}"],
            "tool_filter": ["read_file", "list_directory"]
        },
        "remote-mcp": {
            "url": "https://example.com/mcp",
            "headers": {
                "Authorization": "Bearer ${env:MCP_AUTH_TOKEN}"
            }
        },
        "remote-sse": {
            "url": "https://example.com/sse",
            "headers": {
                "Authorization": "Bearer ${env:MCP_AUTH_TOKEN}"
            }
        }
    }
}
```

Notes:

- MCP toolsets are loaded once at startup from `MCP_CONFIG_PATH` (default: `mcpServers.json`).
- If the config file is missing, the app starts normally without MCP tools.
- If one MCP server fails to load, the others still load.
- MCP toolsets are closed during app shutdown.

## Architecture (high level)

Slack (UI) → **Bolt app** (Socket Mode, listeners) → **Google ADK** (LlmAgent + sub-agents + local tools + MCP tools, session store) → **Gemini API**. Each Slack thread maps to one ADK session; responses are streamed back.

## Demos

**Search, weather tool, threads & mentions**

<video src="https://github.com/user-attachments/assets/80def011-080a-4673-97f8-1ecd5f84e45d" width="640" controls></video>

**Python code execution via sub-agent**

<video src="https://github.com/user-attachments/assets/287b5c93-624a-4cc3-9b3a-8f6cd0d43d97" width="640" controls></video>

## Roadmap

- [x] MCP (Model Context Protocol) tools
- [ ] Memory Bank across sessions
- [ ] Agent Engine / Cloud Run deployment
- [ ] Observability (e.g. OpenTelemetry)
- [ ] A2A protocol for multi-agent workflows

## License

[MIT](LICENSE)

## Acknowledgments

Built on [Slack’s bolt-python-assistant-template](https://github.com/slack-samples/bolt-python-assistant-template) and [Google ADK](https://google.github.io/adk-docs/). A capstone version lives on the [`kaggle-project`](https://github.com/jonigl/sladk-agents/tree/kaggle-project) branch and was also shared in the [5-Day AI Agents Intensive with Google](https://www.kaggle.com/learn-guide/5-day-agents) capstone.

---

Made with ❤️ by jonigl
