# OpenWebUI Agentic Tooling Suite

[![Version](https://img.shields.io/badge/version-1.2.7-blue.svg)](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup/releases)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![OpenWebUI](https://img.shields.io/badge/OpenWebUI-compatible-orange.svg)](https://openwebui.com)
[![License](https://img.shields.io/badge/license-GPL-red.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/ShaoRou459/OpenwebUI-Tooling-Setup?style=social)](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup/stargazers)

**Intelligent tool routing and autonomous AI capabilities for OpenWebUI**

📦 **OpenWebUI Marketplace**: [Auto Tool Router](https://openwebui.com/f/sdjfhsud/auto_tool_router) | [Exa Search Router](https://openwebui.com/t/sdjfhsud/exa_router_search)

[中文 Readme](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup/blob/main/README_zh.md) | [Quick Start](#installation--setup) | [Configuration Guide](#configuration)

---

## Overview

The OpenWebUI Agentic Tooling Suite transforms your local AI models from passive chat interfaces into intelligent, autonomous assistants. The suite includes the **Auto Tool Selector** (v1.2.7), **Exa Search Router** (v1.2.5), and the **Agentic Master Tool** (v2.1.0 Beta), featuring enhanced debugging, flexible architecture, and improved accessibility for both vision and non-vision models.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **🤖 Autonomous Tool Selection** | Automatically routes user queries to the most appropriate tool without manual intervention |
| **🔍 Multi-Modal Search** | Three search modes: **Crawl** (specific URLs), **Standard** (quick research), **Complete** (deep analysis) |
| **🎨 Intelligent Image Generation** | Auto-optimizes prompts and seamlessly integrates generated images into conversations |
| **💻 Dual Code Execution** | Support for both Jupyter notebooks and basic Python code interpretation |
| **👁️ Universal Vision** | Non-vision models gain image understanding through automatic transcription |
| **🔧 Advanced Debugging** | Comprehensive logging system for troubleshooting and optimization |
| **⚡ Real-Time Status** | Live progress updates throughout tool execution |

---

## Architecture

The suite offers two architectural approaches:

### Approach 1: Automatic Routing (Recommended for most users)

1. **Auto Tool Selector** (Function): Master router that analyzes queries and selects appropriate tools
2. **Exa Search Router** (Tool): Advanced search capabilities with fallback to native OpenWebUI search

![Architecture Diagram](https://github.com/user-attachments/assets/e79f7658-020f-4804-8d16-e4414ad781e8)

### Approach 2: Agentic Master Tool (Beta - For advanced agentic models)

**Agentic Master Tool** *(Beta)*: A unified tool that exposes all capabilities as directly-callable functions for agentic models like GPT-4o, Claude Sonnet 4/4.5, o3, and other tool-using models.

**Key Differences:**

| Feature | Auto Tool Selector | Agentic Master Tool |
|---------|-------------------|---------------------|
| **Decision Making** | Middleware decides | Model decides |
| **Tool Calls** | Implicit/hidden | Explicit/visible |
| **Transparency** | Lower | Higher |
| **Best For** | All models | Agentic models with strong tool use |

📖 **Learn More**: See [master_tool/README.md](master_tool/README.md) for detailed documentation and examples.

---

## Installation & Setup

> **Choose Your Approach:** Install either the **Auto Tool Selector** (automatic routing) OR the **Agentic Master Tool** (explicit tool calls). For most users, start with Auto Tool Selector.

### Prerequisites

Ensure you have Docker access to your OpenWebUI instance.

### Step 1: Install Dependencies

```bash
docker exec -it open-webui bash
pip install exa_py
exit
docker restart open-webui
```

### Step 2: Choose Your Installation Path

#### Option A: Auto Tool Selector (Recommended for most users)

1. **Install Auto Tool Selector (Function)**:
   - Go to **Admin Settings → Functions → New Function**
   - Copy and paste the contents of `auto_tool_selector.py`
   - Save the function
   - If you plan to use Jupyter Lab as the code interpreter, please download the uploader.py and place it in the home directory of Jupyter.

2. **Install Exa Search Router (Tool)** *(Optional)*:
   - Go to **Workspace → Tools → New Tool**
   - Copy and paste the contents of `exa_router_search.py`
   - **Important**: Set Tool ID to `exa_router_search`
   - Save the tool

3. **Configure Settings**:
   - In your model settings, enable only the **Auto Tool Selector** function
   - Do not enable the Exa Search Router tool directly
   - Configure API keys, models, and behavior options as needed

#### Option B: Agentic Master Tool (Beta - For advanced agentic models)

1. **Install Agentic Master Tool**:
   - Go to **Workspace → Tools → New Tool**
   - Copy and paste the contents of `master_tool/agentic_master_tool.py`
   - Save the tool

2. **Configure Settings**:
   - Enable the **Agentic Master Tool** in your chat
   - Set your `exa_api_key` in the tool's valves
   - Configure other settings as needed (defaults are sensible)

3. **Use with agentic models**:
   - Works best with GPT-4o, Claude Sonnet 4/4.5, o3, or other tool-using models
   - The model will explicitly call tools like `web_search(query="...", mode="STANDARD")`
   - **Note**: Code interpreter is handled via OpenWebUI's native feature (Admin → Settings), not through this tool

📖 **Full Guide**: See [master_tool/README.md](master_tool/README.md) for detailed instructions and examples.

---

## Configuration

### Auto Tool Selector Settings

| Setting | Purpose | Recommendation |
|---------|---------|----------------|
| `helper_model` | Decides which tool to use for queries | GPT-4o-mini, o4-mini, Gemini 2.5 Flash |
| `vision_model` | Analyzes images for non-vision models | GPT-4o, o3, Gemini 2.5 Pro |
| `vision_injection_models` | List of non-vision models to enhance | Add your model IDs (comma-separated) |
| `use_exa_router_search` | Enable advanced Exa search vs native search | `true` (if Exa tool is installed) |
| `debug_enabled` | Enable detailed debug logging | `false` (enable for troubleshooting) |
| `use_jupyter_code_interpreter` | Use Jupyter vs basic code execution | `true` (recommended) |

### Exa Search Router Settings *(If Installed)*

| Setting | Purpose | Recommendation |
|---------|---------|----------------|
| `exa_api_key` | **Required**: Your Exa.ai API key | Get yours at [exa.ai](https://exa.ai) |
| `router_model` | Chooses search strategy (Crawl/Standard/Complete) | GPT-4o-mini, o4-mini, Gemini 2.5 Flash |
| `quick_search_model` | Handles standard search operations | GPT-4o-mini, o4-mini, Gemini 2.5 Flash |
| `complete_agent_model` | Powers deep research analysis | o3, o3-pro, Gemini 2.5 Pro, Claude Sonnet 4 |
| `complete_summarizer_model` | Creates final comprehensive summaries | Gemini 2.5 Pro, GPT-4o, Claude Sonnet 4.5 |
| `debug_enabled` | Enable search operation debugging | `false` (enable for troubleshooting) |

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

### Search Modes

- **Crawl Mode**: `"What does this article say? https://example.com/article"`
- **Standard Mode**: `"What are the benefits of renewable energy?"` (default for most queries)
- **Complete Mode**: `"Do a deep research comparison of React vs Vue.js frameworks"` (requires explicit request)

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

**Search failing**: If using Exa search, verify your API key is set correctly. The system will fall back to native search if Exa is unavailable.

**Vision not working**: Ensure `vision_model` is set and your model ID is listed in `vision_injection_models`.

---

## Update Log

### Agentic Master Tool v2.1.0 (Beta)
- **New**: Fully self-contained tool with embedded Exa search functionality
- **New**: Comprehensive color-coded debug logging to Docker logs
- **Changed**: Removed code_interpreter from tool (use OpenWebUI's native code interpreter instead)
- **Improved**: Better error handling and API compatibility with exa-py v2.0.0+

### Auto Tool Selector v1.2.7 (Current)
- **New**: Built-in image generation using OpenWebUI's native pipeline
- **Improved**: Enhanced debugging with performance metrics
- **Improved**: Better conversation history handling for tool routing

### Exa Search Router v1.2.5
- **Improved**: Enhanced Exa API compatibility
- **Improved**: Better error handling and graceful fallback to native search
- **Fixed**: Query optimization for current year search terms

### Version 1.1
- **New**: Enhanced debugging system with color-coded logging
- **New**: Vision model integration for non-vision models
- **New**: Modular search architecture with native OpenWebUI fallback
- **New**: Choice between Jupyter and basic code interpreters
- **New**: Settings-based configuration (no more manual file management)
- **Improved**: More robust error handling and retry mechanisms
- **Improved**: Better status updates and user feedback

### Version 1.0
- Initial release with autonomous tool routing
- Basic search, image generation, and code interpretation
- Manual configuration through separate files

---

## FAQ

**Q: Do I need the Exa Search Router tool?**
A: No, it's optional. The Auto Tool Selector will fall back to OpenWebUI's native search if Exa is not available.

**Q: Why use Jupyter over basic code interpreter?**
A: Jupyter provides a full notebook environment with file persistence, better for complex analysis and data work.

**Q: Can I use this with any OpenWebUI model?**
A: Yes, the Auto Tool Selector works with any model. Vision enhancement works best with models that support tool calling. The Agentic Master Tool works best with capable agentic models like GPT-4o, Claude Sonnet 4/4.5, and o3.

**Q: How do I know if tools are working?**
A: Enable debug mode and check Docker logs. You'll see detailed color-coded information about tool selection and execution.

**Q: What happened to code_interpreter in the Agentic Master Tool?**
A: Code interpreter has been removed from the Agentic Master Tool (v2.1.0+) because tools cannot set the required OpenWebUI feature flags. Enable code interpreter globally in OpenWebUI Admin → Settings instead.

**Q: Which models should I use for best results?**
A: For routing/helper tasks: GPT-4o-mini, o4-mini, or Gemini 2.5 Flash. For deep research (COMPLETE mode): o3, o3-pro, Gemini 2.5 Pro, or Claude Sonnet 4. For vision: GPT-4o, o3, or Gemini 2.5 Pro.

---

## License & Support

- **Author**: ShaoRou459
- **GitHub**: [OpenwebUI-Tooling-Setup](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup)
- **Issues**: Report bugs and request features via GitHub Issues
---

*Transform your AI from reactive to proactive with intelligent tool routing and autonomous capabilities.*
