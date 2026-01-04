# Project Summary: OpenWebUI Agentic Tooling Suite

## Overview

This project provides intelligent tool routing and autonomous AI capabilities for OpenWebUI. It transforms local AI models from passive chat interfaces into intelligent assistants that can automatically select and use the right tools for each task.

**Author:** ShaoRou459
**Repository:** [OpenwebUI-Tooling-Setup](https://github.com/ShaoRou459/OpenwebUI-Tooling-Setup)

---

## Core Components (3 Python Files)

### 1. Auto Tool Selector (`auto_tool_selector.py`)
**Version:** 1.2.7
**Type:** OpenWebUI Function (Middleware/Filter)

**Purpose:** Master router that intercepts user messages and automatically decides which tool to use based on the query content and conversation context.

**Key Capabilities:**
- **Intelligent Routing:** Uses an LLM to analyze queries and route to the appropriate handler
- **Image Generation:** Integrates with OpenWebUI's native image generation pipeline
- **Code Interpreter:** Supports both Jupyter notebook and basic Python execution modes
- **Vision Enhancement:** Allows non-vision models to understand images by transcribing them via a vision model
- **Memory Handler:** Stores/retrieves user information via code interpreter

**Tool Routing Options:**
| Tool ID | Purpose |
|---------|---------|
| `web_search` / `exa_router_search` | Web searches (configurable) |
| `image_generation` | Image creation requests |
| `code_interpreter` | Python code execution |
| `memory` | Conversational memory storage |

**Configuration (Valves):**
- `helper_model` - LLM for routing decisions
- `vision_model` - Model to describe images for non-vision models
- `vision_injection_models` - List of model IDs to receive image transcriptions
- `use_exa_router_search` - Toggle between Exa and native web search
- `use_jupyter_code_interpreter` - Toggle Jupyter vs basic code execution
- `debug_enabled` - Enable detailed logging

---

### 2. Exa Router Search (`exa_router_search.py`)
**Version:** 1.2.5
**Type:** OpenWebUI Tool
**Dependency:** `exa_py` (Exa.ai API client)

**Purpose:** Advanced web search tool with three distinct search strategies and an iterative research system.

**Search Modes:**
| Mode | Use Case | Description |
|------|----------|-------------|
| **CRAWL** | Specific URL provided | Directly fetches and returns content from a given URL |
| **STANDARD** | Quick lookups | Single search, crawl top results, synthesize answer |
| **COMPLETE** | Deep research | Multi-iteration agentic research with reasoning loops |

**COMPLETE Mode Flow:**
1. Generate introductory query for context
2. Set research objectives and direction
3. Iterative search loops with reasoning (configurable max iterations)
4. Final synthesis of all findings

**Configuration (Valves):**
- `exa_api_key` - Required API key for Exa.ai
- `router_model` - Decides CRAWL/STANDARD/COMPLETE
- `quick_search_model` - Handles STANDARD path
- `complete_agent_model` - Powers COMPLETE path reasoning
- `complete_summarizer_model` - Creates final summaries
- `quick_urls_to_search` / `quick_queries_to_crawl` - STANDARD mode limits
- `complete_urls_to_search_per_query` / `complete_queries_to_crawl` / `complete_max_search_iterations` - COMPLETE mode settings
- `debug_enabled` - Enable detailed logging
- `show_sources` - Toggle source display in UI

---

### 3. Jupyter Uploader (`jupyter_uploader.py`)
**Type:** Utility Script

**Purpose:** Simple helper for uploading files from Jupyter notebook environment to OpenWebUI's file storage API.

**Usage:**
```python
import uploader
link = uploader.upload_file("myfile.pdf")
print(link)  # Returns public URL
```

**Configuration:**
- `TOKEN` - OpenWebUI API token
- `BASE_URL` - OpenWebUI instance URL

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────┐
│   Auto Tool Selector    │  (Function/Filter)
│   - Analyzes query      │
│   - Routes to handler   │
└───────────┬─────────────┘
            │
    ┌───────┼───────┬───────────────┐
    ▼       ▼       ▼               ▼
┌───────┐ ┌───────┐ ┌─────────────┐ ┌────────┐
│ Image │ │ Code  │ │ Web Search  │ │ Memory │
│  Gen  │ │Interp.│ │ (Exa/Native)│ │        │
└───────┘ └───────┘ └─────────────┘ └────────┘
```

---

## Shared Features

### Debug System
Both main tools include an enhanced debug system with:
- Color-coded ANSI logging to stderr
- Session tracking with unique IDs
- Timing metrics for operations
- LLM call tracking (count, duration, failures)
- URL/search metrics
- Error and warning collection
- Comprehensive metrics summary at end of execution

### Retry Mechanisms
- `generate_with_retry()` - Exponential backoff for LLM calls
- `generate_with_parsing_retry()` - Combines API retry with response validation
- `_extract_with_correction()` - Re-prompts LLM if output format is invalid

### Status Updates
Real-time status messages sent via `__event_emitter__` to show users what the system is doing.

---

## Installation Requirements

1. **Python Dependencies:**
   ```bash
   pip install exa_py
   ```

2. **OpenWebUI Setup:**
   - Auto Tool Selector: Install as Function
   - Exa Router Search: Install as Tool (ID must be `exa_router_search`)
   - Jupyter Uploader: Place in Jupyter's home directory

---

## File Summary

| File | Lines | Type | Version |
|------|-------|------|---------|
| `auto_tool_selector.py` | ~1150 | Function | 1.2.7 |
| `exa_router_search.py` | ~2090 | Tool | 1.2.5 |
| `jupyter_uploader.py` | ~24 | Utility | - |

---

*Note: The `master_tool/` directory contains a beta version of an alternative agentic approach and is not covered in this summary.*
