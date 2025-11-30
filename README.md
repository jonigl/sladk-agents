# Sladk Agents

**Your company's Slack AI agents of the new era of generative AI powered by Google Agent Development Kit (ADK)**

[![Track: Enterprise Agents](https://img.shields.io/badge/Track-Enterprise%20Agents-blue)](https://www.kaggle.com/competitions/agents-intensive-capstone-project/overview/tracks-and-awards)
[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Gemini-orange)](https://ai.google.dev/)
[![Google ADK](https://img.shields.io/badge/Google-ADK-green)](https://google.github.io/adk-docs/)
[![Slack Bolt](https://img.shields.io/badge/Slack-Bolt%20for%20Python-purple)](https://docs.slack.dev/tools/bolt-python)

---

## 📑 Table of Contents

- [🎯 The Problem](#-the-problem)
- [💡 The Solution](#-the-solution)
- [🏗️ Architecture](#️-architecture)
- [✨ Key Features Implemented (ADK Concepts)](#-key-features-implemented-adk-concepts)
- [🚀 Setup & Installation](#-setup--installation)
- [🎮 Usage](#-usage)
- [🖥️ Demos](#️-demos)
- [🔧 Extending the Agent](#-extending-the-agent)
- [📊 Impact & Value](#-impact--value)
- [🛣️ Future Roadmap](#️-future-roadmap)
- [📚 References](#-references)
- [📜 License](#-license)
- [👤 Author](#-author)
- [🙏 Acknowledgments](#-acknowledgments)

---

## 🎯 The Problem

Enterprise teams rely heavily on Slack for daily collaboration—sharing updates, asking questions, coordinating projects, and making decisions. However, accessing AI-powered assistance typically requires:

- **Context switching**: Leaving Slack to use external AI tools (Gemini web, chatGPT, etc.)
- **Manual copy-paste workflows**: Moving conversation context between platforms
- **Lost productivity**: Teams lose time switching between tools
- **Fragmented knowledge**: AI insights don't stay where the work happens

While Slack recently introduced [AI Agents](https://docs.slack.dev/ai/) as a native feature, building production-ready agents still requires significant integration work, especially when leveraging advanced AI frameworks.

## 💡 The Solution

**Sladk Agents** bridges the gap between Slack's native AI Agent capabilities and Google's powerful [Agent Development Kit (ADK)](https://google.github.io/adk-docs/). It provides a ready-to-deploy framework that enables enterprises to:

- Deploy AI agents directly within Slack's native UI (side panel, threads, mentions)
- Leverage Google ADK's multi-agent architecture with sub-agents for specialized tasks
- Maintain conversation context through session management
- Extend functionality with built-in and custom tools
- Stream responses in real-time for a seamless user experience

**Key Value Proposition**: Teams can now access sophisticated AI assistance exactly where they collaborate—no context switching, no copy-paste, just intelligent help when and where they need it.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SLACK WORKSPACE                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Side Panel │  │   Threads   │  │  @mentions  │  │   Direct Messages   │ │
│  │  Assistant  │  │             │  │             │  │                     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          └────────────────┴────────────────┴────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SLADK AGENTS (Bolt for Python)                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          AsyncApp + Socket Mode                        │ │
│  │  • Real-time WebSocket connection to Slack                             │ │
│  │  • Async handlers for non-blocking operations                          │ │
│  │  • Native streaming support (chat_stream)                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                           LISTENERS                                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  Assistant   │  │    Events    │  │   Actions    │                  │ │
│  │  │  • started   │  │  • mentions  │  │  • feedback  │                  │ │
│  │  │  • message   │  │              │  │              │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE ADK (Agent Layer)                            │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         LlmAgent (Root Agent)                          │ │
│  │  • Model: Gemini 2.5 Flash (configurable)                              │ │
│  │  • Custom system instructions                                          │ │
│  │  • Safety settings & temperature control                               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                    │                    │                    │              │
│                    ▼                    ▼                    ▼              │
│  ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ │
│  │    SearchAgent       │ │     CodeAgent        │ │   Custom Tools       │ │
│  │  (Sub-Agent)         │ │   (Sub-Agent)        │ │                      │ │
│  │  ┌────────────────┐  │ │  ┌────────────────┐  │ │  ┌────────────────┐  │ │
│  │  │ google_search  │  │ │  │ Code Executor  │  │ │  │  get_weather   │  │ │
│  │  └────────────────┘  │ │  └────────────────┘  │ │  │  (wttr.in)     │  │ │
│  └──────────────────────┘ └──────────────────────┘ │  └────────────────┘  │ │
│                                                    │  ┌────────────────┐  │ │
│                                                    │  │  + extensible  │  │ │
│                                                    │  └────────────────┘  │ │
│                                                    └──────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        SESSION MANAGEMENT                              │ │
│  │  • InMemorySessionService: Maintains conversation state per thread     │ │
│  │  • Context Compaction: Efficient token usage (interval=5, overlap=1)   │ │
│  │  • User/Session ID mapping: Slack thread_ts → ADK session              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                              RUNNER                                    │ │
│  │  • Async execution with run_async()                                    │ │
│  │  • Streaming response chunks to Slack                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            GEMINI API                                       │
│                     (Generative AI Backend)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## ✨ Key Features Implemented (ADK Concepts)

This project demonstrates **5 key concepts** from the Google ADK course:

### 1. Multi-Agent System
- **Root Agent (`LlmAgent`)**: Orchestrates user requests and delegates to specialized sub-agents
- **SearchAgent**: Handles web search queries using Google Search tool
- **CodeAgent**: Executes Python code for calculations and data processing

### 2. Tools Integration
- **Built-in Tools**: `google_search` for real-time web information
- **Code Execution**: `BuiltInCodeExecutor` for running Python code
- **Custom Tools**: `get_weather()` function demonstrating extensibility

### 3. Sessions & State Management
- **InMemorySessionService**: Maintains conversation context across messages
- **Session persistence**: Each Slack thread maps to a unique ADK session
- **User isolation**: Sessions are scoped per user and thread

### 4. Context Engineering
- **EventsCompactionConfig**: Optimizes token usage with:
  - `compaction_interval=5`: Compact every 5 events
  - `overlap_size=1`: Maintain context continuity

### 5. Effective Use of Gemini
- **Model**: Gemini 2.5 Flash (configurable via environment)
- **Safety Settings**: Configurable content filtering
- **Streaming**: Real-time response streaming to Slack


## 🚀 Setup & Installation

### Prerequisites

- Python 3.10+
- A Slack workspace with admin permissions
- Google API key with Gemini access

> [!TIP]
> You can obtain a Google API with Gemini in the [Google AI Studio](https://aistudio.google.com/app/api-keys).

### 1. Clone the Repository

```bash
git clone https://github.com/jonigl/sladk-agents.git
cd sladk-agents
```

### 2. Create Slack App

> [!TIP]
> You can also review the original Slack Bolt template [instructions here](SLACK_BOLT_TEMPLATE_README.md#creating-the-slack-app).

1. Go to [api.slack.com/apps/new](https://api.slack.com/apps/new) → "From an app manifest"
2. Select your workspace
3. Paste contents of `manifest.json` → Click **Next** → **Create**
4. Click **Install to Workspace** → **Allow**

### 3. Configure Environment

```bash
cp .env.sample .env
```

Edit `.env` with your credentials:

```bash
# Slack Configuration
SLACK_APP_TOKEN=xapp-...        # Basic Info → App-Level Tokens → connections:write
SLACK_BOT_TOKEN=xoxb-...        # OAuth & Permissions → Bot User OAuth Token

# Google ADK Configuration
GOOGLE_API_KEY=your_google_api_key
AGENT_MODEL=gemini-2.5-flash    # or gemini-2.0-flash, gemini-1.5-pro
AGENT_APP_NAME=Sladk_App
AGENT_NAME=Sladk_AI_Agent

# Optional: Custom system instruction
DEFAULT_SYSTEM_INSTRUCTION="You're a helpful assistant in a Slack workspace..."
```

### 4. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the Agent

```bash
python3 app.py
```

Or using Slack CLI:

```bash
slack run
```

---

## 🎮 Usage

### Configure your Slack Preferences

1. Open Slack → Click your profile picture → **Preferences**
2. Go to **Navigation** → Go to the **App agents & assistants**
3. Click the checkbox for **Show app agents**

<video src="https://github.com/user-attachments/assets/3e2ccd42-95b3-4e54-9687-0129ffe29a26" width="640" controls></video>

### Interact with the Agent

Once running, interact with your agent in three ways:

| Method | How |
|--------|-----|
| **Side Panel** | Click the agent icon in Slack's top right corner to open the AI assistant |
| **@Mention** | Type `@Sladk AI Agent` in any channel |
| **Direct Message** | Send a DM to the bot |

### Example Interactions

- *"Search for the latest news about AI agents"* → Uses SearchAgent
- *"Calculate the compound interest on $1000 at 5% for 10 years"* → Uses CodeAgent
- *"What's the weather in San Francisco?"* → Uses custom get_weather tool

## 🖥️ Demos

### Demo 1

- Using google search built-in with ToolAgent / subagent
- Using a custom tool to get the weather
- Interacting with slack thread messages and mentions

<video src="https://github.com/user-attachments/assets/80def011-080a-4673-97f8-1ecd5f84e45d" width="640" controls></video>

### Demo 2

- Python code execution using dedicated subagent as a tool

<video src="https://github.com/user-attachments/assets/287b5c93-624a-4cc3-9b3a-8f6cd0d43d97" width="640" controls></video>

## 🔧 Extending the Agent

### Adding Custom Tools

Create new tools in `ai/tools/custom_tools.py`:

```python
def my_custom_tool(param: str) -> str:
    """
    Description of what this tool does.
    Args:
        param: Description of parameter
    Returns:
        str: Description of return value
    """
    # Your implementation
    return result
```

Then add to the agent in `ai/llm_caller.py`:

```python
from ai.tools.custom_tools import get_weather, my_custom_tool

agent = LlmAgent(
    # ...
    tools=[get_weather, my_custom_tool, AgentTool(agent=search_agent)],
)
```

## 📊 Impact & Value

| Metric | Improvement |
|--------|-------------|
| **Context Switching** | Eliminated - AI lives in Slack |
| **Response Time** | Real-time streaming responses |
| **Tool Access** | Web search, code execution, custom tools in one place |
| **Session Memory** | Maintains context across conversation |
| **Deployment** | Single Python app, no infrastructure complexity |

## 🛣️ Future Roadmap

- [ ] **Memory Bank Integration**: Long-term memory across sessions
- [ ] **MCP Tools**: Model Context Protocol for external integrations
- [ ] **Agent Engine Deployment**: Cloud Run / Agent Engine deployment
- [ ] **Observability**: Tracing and metrics with OpenTelemetry
- [ ] **A2A Protocol**: Agent-to-agent communication for complex workflows

## 📚 References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Slack AI Apps Documentation](https://docs.slack.dev/ai/)
- [Bolt for Python](https://docs.slack.dev/tools/bolt-python)
- [Gemini API](https://ai.google.dev/)

## 📜 License

This project uses **dual licensing**:

| Component | License | File |
|-----------|---------|------|
| Base code (Slack Bolt template) | MIT License | [LICENSE](LICENSE) |
| Sladk Agents additions (agent logic, architecture, ADK integration) | CC-BY-SA 4.0 | [LICENSE_CAPSTONE](LICENSE_CAPSTONE) |

The base Slack Bolt template code is covered by the **MIT License** (original work by Slack Technologies, LLC). All new agent logic, architecture, and Google ADK integration created for this Capstone project is licensed under **CC-BY-SA 4.0** as required by the Kaggle competition rules.

## 👤 Author

**Jonathan Gastón Löwenstern** - GitHub: [@jonigl](https://github.com/jonigl)

Built with ❤️ for the [Kaggle & Google: Agents Intensive - Capstone Project](https://www.kaggle.com/competitions/agents-intensive-capstone-project) - November 2025

## 🙏 Acknowledgments

- Slack for the [bolt-python-assistant-template](https://github.com/slack-samples/bolt-python-assistant-template) foundation
- Google for the [Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- The [5-Day AI Agents Intensive Course with Google](https://www.kaggle.com/learn-guide/5-day-agents) community for inspiration and guidance
