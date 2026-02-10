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

**Prerequisites:** Python 3.10+, Slack workspace (admin), [Google API key](https://aistudio.google.com/app/api-keys) with Gemini.

```bash
git clone https://github.com/jonigl/sladk-agents.git
cd sladk-agents
cp .env.sample .env
# Edit .env: SLACK_APP_TOKEN, SLACK_BOT_TOKEN, GOOGLE_API_KEY, AGENT_MODEL (e.g. gemini-2.5-flash)
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Slack app:** [Create an app](https://api.slack.com/apps/new) from manifest → paste `manifest.json` → Install to workspace. See [SLACK_BOLT_TEMPLATE_README.md](SLACK_BOLT_TEMPLATE_README.md#creating-the-slack-app) if you need step-by-step.

**Run:**

```bash
python3 app.py
```

Or using Slack CLI:

```bash
slack run
```

Slack: **Preferences → Navigation → App agents & assistants** → enable **Show app agents**. Then use the agent via the side panel, @mention in a channel, or DM.

## Usage

| Where        | How |
|-------------|-----|
| Side panel  | Agent icon (top right) in Slack |
| Channel     | `@YourBotName` in a message |
| DM          | Direct message to the bot |

Example prompts: search the web, run Python snippets, or use built-in tools like weather (see `ai/tools/custom_tools.py`).

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

## Architecture (high level)

Slack (UI) → **Bolt app** (Socket Mode, listeners) → **Google ADK** (LlmAgent + sub-agents + tools, session store) → **Gemini API**. Each Slack thread maps to one ADK session; responses are streamed back.

## Demos

**Search, weather tool, threads & mentions**

<video src="https://github.com/user-attachments/assets/80def011-080a-4673-97f8-1ecd5f84e45d" width="640" controls></video>

**Python code execution via sub-agent**

<video src="https://github.com/user-attachments/assets/287b5c93-624a-4cc3-9b3a-8f6cd0d43d97" width="640" controls></video>

## Roadmap

- [ ] Memory Bank across sessions
- [ ] MCP (Model Context Protocol) tools
- [ ] Agent Engine / Cloud Run deployment
- [ ] Observability (e.g. OpenTelemetry)
- [ ] A2A protocol for multi-agent workflows

## License

[MIT](LICENSE)

## Acknowledgments

Built on [Slack’s bolt-python-assistant-template](https://github.com/slack-samples/bolt-python-assistant-template) and [Google ADK](https://google.github.io/adk-docs/). A capstone version lives on the [`kaggle-project`](https://github.com/jonigl/sladk-agents/tree/kaggle-project) branch and was also shared in the [5-Day AI Agents Intensive with Google](https://www.kaggle.com/learn-guide/5-day-agents) capstone.

---

Made with ❤️ by jonigl