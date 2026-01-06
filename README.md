# OpenWebUI Agentic Tooling Suite

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup/releases)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![OpenWebUI](https://img.shields.io/badge/OpenWebUI-compatible-orange.svg)](https://openwebui.com)
[![License](https://img.shields.io/badge/license-GPL-red.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/ShaoRou459/OpenwebUI-Tooling-Setup?style=social)](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup/stargazers)

**Intelligent tool routing and autonomous AI capabilities for OpenWebUI**

📦 **OpenWebUI Marketplace**: [Auto Tool Router](https://openwebui.com/posts/auto_tool_selecter_add9aede) | [Exa Agentic Search](https://openwebui.com/t/sdjfhsud/exa_router_search)

[中文 Readme](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup/blob/main/README_zh.md) | [Quick Start](#installation--setup) | [Configuration Guide](#configuration) | [Release Notes](RELEASE_NOTES.md)

---

## Overview

The OpenWebUI Agentic Tooling Suite transforms your local AI models from passive chat interfaces into intelligent, autonomous assistants. The suite includes the **Auto Tool Selector** (v1.3.0) and **Exa Agentic Search** (v2.0.0), featuring enhanced debugging, flexible architecture, and improved accessibility for both vision and non-vision models.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Autonomous Tool Selection** | Automatically routes user queries to the most appropriate tool without manual intervention |
| **Agentic Search** | Intelligent iterative search with agent-controlled parameters—adapts search strategy based on query complexity |
| **Intelligent Image Generation** | Auto-optimizes prompts and seamlessly integrates generated images into conversations |
| **Dual Code Execution** | Support for both Jupyter notebooks and basic Python code interpretation |
| **Universal Vision** | Non-vision models gain image understanding through automatic transcription |
| **Advanced Debugging** | Comprehensive logging system with session summaries and metrics |
| **Real-Time Status** | Live progress updates throughout tool execution |

---

## Architecture

1. **Auto Tool Selector** (Function): Master router that analyzes queries and selects appropriate tools
2. **Exa Agentic Search** (Tool): Intelligent agentic search with full parameter control and iterative research

![Architecture Diagram](https://github.com/user-attachments/assets/e79f7658-020f-4804-8d16-e4414ad781e8)

---

## Installation & Setup

### Prerequisites

Ensure you have Docker access to your OpenWebUI instance.

### Step 1: Install Dependencies

```bash
docker exec -it open-webui bash
pip install exa_py
exit
docker restart open-webui
```

### Step 2: Install Components

1. **Install Auto Tool Selector (Function)**:
   - Go to **Admin Settings → Functions → New Function**
   - Copy and paste the contents of `auto_tool_selector.py`
   - Save the function
   - If you plan to use Jupyter Lab as the code interpreter, please download the uploader.py and place it in the home directory of Jupyter.

2. **Install Exa Agentic Search (Tool)** *(Optional but recommended)*:
   - Go to **Workspace → Tools → New Tool**
   - Copy and paste the contents of `exa_agentic_search.py`
   - **Important**: Set Tool ID to `exa_agentic_search`
   - Save the tool

3. **Configure Settings**:
   - In your model settings, enable only the **Auto Tool Selector** function
   - Do not enable the Exa Agentic Search tool directly (it's called by the Auto Tool Selector)
   - Configure API keys, models, and behavior options as needed

---
## Configuration

### Auto Tool Selector Settings

| Setting | Purpose | Recommendation |
|---------|---------|----------------|
| `helper_model` | Decides which tool to use for queries | GPT-4o-mini, o4-mini, Gemini 2.5 Flash |
| `vision_model` | Analyzes images for non-vision models | GPT-4o, o3, Gemini 2.5 Pro |
| `vision_injection_models` | List of non-vision models to enhance | Add your model IDs (comma-separated) |
| `use_exa_agentic_search` | Enable agentic Exa search vs native search | `true` (if Exa tool is installed) |
| `debug_enabled` | Enable detailed debug logging | `false` (enable for troubleshooting) |
| `use_jupyter_code_interpreter` | Use Jupyter vs basic code execution | `true` (recommended) |

### Exa Agentic Search Settings *(If Installed)*

| Setting | Purpose | Recommendation |
|---------|---------|----------------|
| `exa_api_key` | **Required**: Your Exa.ai API key | Get yours at [exa.ai](https://exa.ai) |
| `agent_model` | LLM for agentic search (evaluation, query generation) | GPT-4o-mini, o4-mini, Gemini 2.5 Flash |
| `max_iterations` | Maximum search iterations before returning | 3 (default) |
| `debug_enabled` | Enable search operation debugging | `false` (enable for troubleshooting) |
| `show_sources` | Display source citations in UI | `false` (optional) |

---

## Usage Examples

### Autonomous Tool Selection
```
User: "What's the latest news about AI developments today?"
→ Automatically routes to web search, finds current articles, synthesizes response

User: "Create a logo for my coffee shop called 'Morning Brew'"
→ Automatically routes to image generation, optimizes prompt, generates and displays image

User: "Analyze this sales data and create a visualization"
→ Automatically routes to code interpreter, processes data, creates charts
```

### Agentic Search

The new Exa Agentic Search automatically adapts its search strategy based on query complexity:

- **Simple queries**: Quick, focused search with early stopping
- **Research queries**: Multi-iteration search with comprehensive synthesis
- **The agent controls**: Search type, category filters, date ranges, domain filters, and result counts

### Vision Enhancement
Non-vision models can now process images when you include them in your messages. The system automatically describes images and provides that context to the model.

---

## Troubleshooting

### Enable Debug Mode
Set `debug_enabled` to `true` in your function/tool settings to see detailed logs in your Docker container:

```bash
docker logs open-webui -f
```

### Common Issues

**Tool not activating**: Check that only the Auto Tool Selector function is enabled in model settings, not the individual tools.

**Search failing**: If using Exa search, verify your API key is set correctly and the exa_py package is installed. The system will fall back to native search if Exa is unavailable.

**Vision not working**: Ensure `vision_model` is set and your model ID is listed in `vision_injection_models`.

---

## Update Log

### Exa Agentic Search v2.0.0 (Current) 🆕
- **New**: Complete rewrite with agentic architecture—AI controls all search parameters
- **New**: Iterative research with intelligent stopping criteria
- **New**: Standardized output format (EXTRACTED_INFO → EVALUATION → DECISION → SEARCH_CONFIG)
- **New**: Redesigned debug system with clean session summaries and metrics
- **Improved**: Single API call efficiency with `search_and_contents`
- **Replaces**: `exa_router_search.py` (now deprecated)

### Auto Tool Selector v1.3.0 (Current)
- **Improved**: Better LLM response parsing with JSONResponse support
- **Improved**: Enhanced retry logic with exponential backoff
- **Improved**: Better conversation history handling for tool routing

### Previous Versions
- See [RELEASE_NOTES.md](RELEASE_NOTES.md) for full version history

---

## FAQ

**Q: Do I need the Exa Agentic Search tool?**
A: No, it's optional. The Auto Tool Selector will fall back to OpenWebUI's native search if Exa is not available. However, the agentic search provides much better research capabilities.

**Q: Why use Jupyter over basic code interpreter?**
A: Jupyter provides a full notebook environment with file persistence, better for complex analysis and data work.

**Q: Can I use this with any OpenWebUI model?**
A: Yes, the Auto Tool Selector works with any model. Vision enhancement works best with models that support tool calling.

**Q: How do I know if tools are working?**
A: Enable debug mode and check Docker logs. You'll see detailed color-coded information about tool selection and execution.

**Q: Which models should I use for best results?**
A: For most tasks, including routing and searching: GPT-5 Mini, Gemini 3 Flash, Claude 4.5 Haiku will suffice. 
---

*Transform your AI from reactive to proactive with intelligent tool routing and autonomous capabilities.*
