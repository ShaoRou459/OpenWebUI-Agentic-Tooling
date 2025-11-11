# OpenWebUI Separate Tools

This directory contains individual, specialized OpenWebUI tools extracted from the master tool suite. Each tool is designed to work independently and can be called directly by AI models that support native tool calling.

## 🎯 Purpose

These tools have been separated for:
1. **Better customization** - Each tool can be configured independently
2. **Direct model invocation** - Models like GPT-4o and Claude 3.5+ can call these tools directly
3. **Simpler architecture** - No need for internal routing logic
4. **Enhanced AI responses** - Tools are optimized for AI model consumption

## 📦 Available Tools

### 1. **crawl_url.py** - URL Content Crawler
Crawls and extracts content from a specific URL using Exa.

**Method:** `crawl_url(url: str)`

**Example:**
```python
await crawl_url("https://example.com/article")
```

**Use cases:**
- Extract content from documentation pages
- Read articles or blog posts
- Fetch specific web page content

**Configuration (Valves):**
- `exa_api_key`: Your Exa API key

---

### 2. **web_search.py** - Web Search Tool
Quick web search with multiple sources (optimized for AI consumption).

**Method:** `web_search(query: str)`

**Key Features:**
- **NO internal query refinement** - The calling AI model should provide an optimized search query
- Returns structured, formatted results optimized for AI analysis
- Includes metadata, sources, and instructions for the AI model

**Example:**
```python
# The AI model should optimize the query before calling:
await web_search("latest AI developments 2025")  # Good
await web_search("what's happening with AI?")     # Bad - not optimized
```

**Configuration (Valves):**
- `exa_api_key`: Your Exa API key
- `urls_to_search`: Number of URLs to fetch (default: 5)
- `urls_to_crawl`: Number of top URLs to crawl (default: 3)
- `max_content_chars`: Maximum content to return (default: 12000)

**Response Format:**
```markdown
# Web Search Results
**Query:** [search query]
**Sources Retrieved:** [count]
**Total Content:** [character count]

---

## Source 1: [Title]
**URL:** [url]
**Domain:** [domain]

**Content:**
[Full content from source]

---

**Instructions for AI Model:**
- Analyze the above sources to answer the user's question
- Synthesize information across multiple sources
- Cite specific sources when making claims
...
```

---

### 3. **deep_research.py** - Deep Research Tool (Multi-Agent)
Comprehensive parallel multi-agent research system with independent specialized sub-agents.

**Method:** `deep_research(query: str)`

**Key Features:**
- **Parallel Multi-Agent Architecture** - Launches multiple specialized sub-agents simultaneously
- **AI-Defined Goals** - Coordinator model defines research goal and identifies objectives
- **Independent Sub-Agents** - Each sub-agent researches a distinct objective (2-5 objectives)
- **Iterative Reasoning** - Each sub-agent conducts up to 3 rounds of research with reasoning
- **Comprehensive Synthesis** - Master synthesizer combines all findings into holistic knowledge base

**Architecture:**
```
1. AI defines research goal
   ↓
2. Identifies 2-5 distinct research objectives
   ↓
3. Launches parallel sub-agents (one per objective)
   ├─ Sub-Agent 1 → Rounds 1-3 → Findings
   ├─ Sub-Agent 2 → Rounds 1-3 → Findings
   ├─ Sub-Agent 3 → Rounds 1-3 → Findings
   ├─ Sub-Agent 4 → Rounds 1-3 → Findings
   └─ Sub-Agent 5 → Rounds 1-3 → Findings
   ↓
4. Synthesizer combines all findings
   ↓
5. Returns comprehensive knowledge base
```

**Example:**
```python
await deep_research("What are the latest developments in quantum computing and their practical applications?")
```

**Configuration (Valves):**
- `exa_api_key`: Your Exa API key
- `coordinator_model`: Model for goal definition and objective identification (default: gpt-4-turbo)
- `sub_agent_model`: Model for sub-agent reasoning and research (default: gpt-4-turbo)
- `synthesizer_model`: Model for final synthesis of all findings (default: gpt-4-turbo)
- `max_objectives`: Maximum number of parallel research objectives, 2-5 (default: 5)
- `sub_agent_max_rounds`: Maximum research rounds per sub-agent (default: 3)
- `queries_per_round`: Number of search queries per sub-agent round (default: 2)
- `urls_per_query`: URLs to fetch per query (default: 5)
- `urls_to_crawl`: URLs to crawl per query (default: 3)

**Research Process:**
1. **Goal Definition** - AI analyzes question and defines research goal
2. **Objective Identification** - AI identifies 2-5 distinct research areas
3. **Parallel Research** - Multiple sub-agents research simultaneously:
   - Each sub-agent focuses on one specific objective
   - Each conducts up to 3 rounds of research
   - Each round: reasoning → query generation → search → analysis
   - Sub-agents work independently and in parallel
4. **Final Synthesis** - Master synthesizer combines all sub-agent findings

**When to Use:**
- Complex questions requiring multiple perspectives
- Multi-faceted topics needing comprehensive coverage
- Research requiring deep domain exploration
- Questions with multiple distinct components

---

### 4. **image_generation.py** - Image Generation Tool
Generate images from text prompts using AI models.

**Method:** `generate_image(prompt: str, description: str = None)`

**Example:**
```python
await generate_image(
    prompt="A serene mountain landscape at sunset with purple and orange skies",
    description="Mountain sunset"
)
```

**Configuration (Valves):**
- `image_gen_model`: Model for image generation (default: gpt-4o-image)

**Returns:**
Markdown-formatted image with URL and caption:
```markdown
![Mountain sunset](https://example.com/image.png)

*Mountain sunset*
```

---

## 🚀 Installation & Usage

### 1. Copy to OpenWebUI

Copy the tool files to your OpenWebUI tools directory:
```bash
cp separate_tools/*.py /path/to/openwebui/tools/
```

### 2. Configure API Keys

Each tool that uses Exa needs an API key:
1. Open OpenWebUI admin panel
2. Navigate to Tools settings
3. Find each tool and configure the `exa_api_key` valve
4. Optionally adjust other configuration parameters

### 3. Enable Tools

Enable the tools you want to use in your OpenWebUI instance.

### 4. Use with AI Models

These tools are designed to be called directly by AI models that support tool calling:

**Example conversation:**
```
User: Search the web for the latest news on quantum computing

AI: [Calls web_search("latest quantum computing news 2025")]

User: Generate an image of a quantum computer

AI: [Calls generate_image("photorealistic quantum computer with glowing qubits")]
```

---

## 🔍 Key Differences from Master Tool

### Web Search Tool
- **Old (Master Tool):** Internally refined search queries using an LLM
- **New (Separate Tool):** AI model provides optimized query directly
- **Benefit:** Faster, more transparent, better control

### Response Formatting
- **Old:** Simple text responses
- **New:** Structured markdown with metadata, sources, and AI instructions
- **Benefit:** Better AI comprehension and synthesis

### Tool Selection
- **Old:** Router decides which mode to use
- **New:** AI model directly chooses the appropriate tool
- **Benefit:** More explicit, easier to debug, better for agentic workflows

---

## ✅ Testing & Validation

Run the validation script to verify all tools:
```bash
cd separate_tools
python validate_tools.py
```

This checks:
- Python syntax validity
- Proper OpenWebUI tool structure
- Complete docstrings
- Async method signatures
- Required classes and methods

---

## 📊 Comparison Matrix

| Feature | Master Tool | Separate Tools |
|---------|-------------|----------------|
| Tool selection | Internal router | Model decides |
| Query refinement | Internal LLM | Model provides optimized query |
| Customization | Global settings | Per-tool settings |
| Response format | Simple text | Structured markdown |
| Transparency | Hidden routing | Explicit tool calls |
| Best for | Simple setups | Agentic workflows |

---

## 🛠️ Development

### Adding New Tools

Follow this structure:
```python
"""
Title: Your Tool Name
Description: What it does
author: Your Name
author_url: https://github.com/yourname
Version: 1.0.0
Requirements: dependencies
"""

from pydantic import BaseModel, Field

class Tools:
    class Valves(BaseModel):
        # Configuration parameters
        pass

    def __init__(self):
        self.valves = self.Valves()

    async def your_tool_method(
        self,
        param: str,
        __event_emitter__: Optional[Callable] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
    ) -> str:
        """
        Tool description.

        Args:
            param: Description

        Returns:
            Result description
        """
        # Implementation
        pass
```

### Testing New Tools

Add your tool to the validation script and run:
```bash
python validate_tools.py
```

---

## 📝 License

Same as the parent project.

---

## 👤 Author

**ShaoRou459**
- GitHub: [@ShaoRou459](https://github.com/ShaoRou459)

---

## 🙏 Acknowledgments

These tools are extracted and enhanced versions of the original OpenWebUI agentic tooling suite, optimized for modern AI models with native tool calling capabilities.
