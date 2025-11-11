# Agentic Master Tool

A unified master tool designed for agentic AI models that exposes all capabilities as directly-callable functions. Instead of automatic middleware routing, the model chooses which tool to use and calls it with specific parameters.

## Philosophy

As AI models become more agentic and capable of tool use, they can make better decisions about which tools to use and when. This master tool embraces that philosophy by:

- **Explicit over implicit**: Model explicitly calls tools with arguments instead of relying on routing middleware
- **Transparency**: Each tool call is visible and auditable
- **Flexibility**: Model can chain multiple tools or call the same tool multiple times with different parameters
- **Simplicity**: One tool to install, multiple capabilities to use

## Available Tools

### 1. Web Search (`web_search`)

Search the web with configurable depth and intelligence levels.

**Modes:**
- `AUTO` - Let the system automatically choose the best search strategy
- `CRAWL` - Extract and read content from a single URL
- `STANDARD` - Quick search with ~5 sources (fast, good for most queries)
- `COMPLETE` - Deep multi-iteration research (comprehensive, slower)

**Usage:**
```python
# Quick search for recent information
await web_search(
    query="latest developments in AI safety",
    mode="STANDARD"
)

# Read content from a specific URL
await web_search(
    query="https://example.com/article",
    mode="CRAWL"
)

# Deep research on a complex topic
await web_search(
    query="comprehensive analysis of renewable energy trends 2024-2025",
    mode="COMPLETE"
)

# Let the system decide (AUTO mode)
await web_search(
    query="what is the weather like today?"
)
```

**Parameters:**
- `query` (str, required): Search query or URL to process
- `mode` (str, optional): "AUTO", "CRAWL", "STANDARD", or "COMPLETE" (default: "AUTO")

### 2. Code Interpreter (`code_interpreter`)

Enable Python/Jupyter code execution in the conversation.

**Modes:**
- Jupyter notebook environment (full featured, recommended)
- Basic Python execution (lightweight)

**Usage:**
```python
# Enable Jupyter notebook environment
await code_interpreter(
    enable=True,
    use_jupyter=True
)

# Enable basic Python execution
await code_interpreter(
    enable=True,
    use_jupyter=False
)
```

**After enabling**, the model can execute Python code:
```xml
<code_interpreter type="code" lang="python">
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title("Sine Wave")
plt.savefig("sine_wave.png")
print("Plot saved!")
</code_interpreter>
```

**Parameters:**
- `enable` (bool, optional): Whether to enable code interpreter (default: True)
- `use_jupyter` (bool, optional): Use Jupyter (True) or basic Python (False). If None, uses valve setting.

### 3. Image Generation (`image_generation`)

Generate images from text descriptions.

**Usage:**
```python
# Generate an image
await image_generation(
    prompt="A serene Japanese garden with cherry blossoms, koi pond, and traditional stone lanterns at sunrise",
    description="Japanese garden at sunrise"
)

# Simple generation
await image_generation(
    prompt="A futuristic city skyline at night with neon lights"
)
```

**Parameters:**
- `prompt` (str, required): Detailed description of the image to generate
- `description` (str, optional): Short caption/title for the image

## Installation

### In OpenWebUI

1. **Upload the tool:**
   - Go to **Workspace → Tools**
   - Click **+ New Tool**
   - Upload `agentic_master_tool.py`

2. **Configure valves:**
   - Set your `exa_api_key` for web search
   - Adjust other settings as needed (most defaults are sensible)

3. **Enable in a chat:**
   - Start a new chat
   - Click the **Tools** icon
   - Enable "Agentic Master Tool"

## Configuration (Valves)

### Web Search Settings

| Valve | Default | Description |
|-------|---------|-------------|
| `exa_api_key` | "" | Your Exa API key (required for web search) |
| `web_search_router_model` | "gpt-4o-mini" | Model for deciding search strategy |
| `web_search_quick_model` | "gpt-4o-mini" | Model for STANDARD mode |
| `web_search_complete_agent_model` | "gpt-4-turbo" | Model for COMPLETE mode reasoning |
| `web_search_complete_summarizer_model` | "gpt-4-turbo" | Model for COMPLETE mode synthesis |
| `web_search_quick_urls` | 5 | URLs to fetch in STANDARD mode |
| `web_search_quick_crawl` | 3 | URLs to read in STANDARD mode |
| `web_search_complete_max_iterations` | 2 | Max research iterations in COMPLETE mode |
| `web_search_show_sources` | false | Show source URLs in results |
| `web_search_debug` | false | Enable detailed debug logging |

### Code Interpreter Settings

| Valve | Default | Description |
|-------|---------|-------------|
| `code_interpreter_use_jupyter` | true | Use Jupyter (true) or basic Python (false) |

### Image Generation Settings

| Valve | Default | Description |
|-------|---------|-------------|
| `image_gen_model` | "gpt-4o-image" | Model for image generation |

## Examples

### Example 1: Research Assistant

```
User: I need to research quantum computing developments

AI: I'll help you research quantum computing developments. Let me do a comprehensive search.

[Calls web_search with mode="COMPLETE"]

Based on my research across multiple sources, here are the key developments in quantum computing...
```

### Example 2: Data Analysis

```
User: Can you analyze this CSV file and create visualizations?

AI: I'll enable the code interpreter to analyze your data.

[Calls code_interpreter with use_jupyter=True]

Now I can process your CSV. Please upload it, and I'll create visualizations using Python.

<code_interpreter type="code" lang="python">
import pandas as pd
import matplotlib.pyplot as plt

# Your data analysis code here
</code_interpreter>
```

### Example 3: Content Creation

```
User: Create an image of a futuristic city and find articles about urban planning

AI: I'll generate the image and search for urban planning articles.

[Calls image_generation with detailed prompt]
[Calls web_search with mode="STANDARD"]

Here's the generated image of a futuristic city:
![Futuristic City](https://...)

And here's what I found about modern urban planning...
```

## Comparison: Master Tool vs Auto Tool Selector

| Feature | Auto Tool Selector | Agentic Master Tool |
|---------|-------------------|---------------------|
| **Decision Making** | Middleware decides | Model decides |
| **Tool Calls** | Implicit/hidden | Explicit/visible |
| **Flexibility** | Fixed routing logic | Model can chain tools freely |
| **Transparency** | Low (middleware black box) | High (visible tool calls) |
| **Complexity** | Higher (routing logic) | Lower (direct calls) |
| **Best For** | Less capable models | Agentic models (GPT-4, Claude 3.5+) |

## Advanced Usage

### Chaining Multiple Tools

The model can call multiple tools in sequence:

```python
# 1. Research the topic
await web_search(query="machine learning best practices", mode="STANDARD")

# 2. Enable code interpreter
await code_interpreter(enable=True)

# 3. Generate example code based on research
# <code_interpreter>...</code_interpreter>

# 4. Create a diagram
await image_generation(prompt="diagram showing ML workflow")
```

### Conditional Tool Use

The model can make intelligent decisions:

```python
# If user asks for a URL specifically
if user_provided_url:
    await web_search(query=url, mode="CRAWL")
else:
    await web_search(query=user_query, mode="STANDARD")
```

### Error Handling

The tools provide detailed error messages:

```
Search failed with error: Exa API key missing. Please set exa_api_key in valves.
```

## Troubleshooting

### Web Search Issues

**Problem:** "Search failed with error: Exa API key missing"
- **Solution:** Set `exa_api_key` in the tool's valves

**Problem:** "Search failed with error: Exa.search() got an unexpected keyword argument"
- **Solution:** Update to exa-py v2.0.0 or later: `pip install --upgrade exa-py`

**Problem:** Generic "no results found" messages
- **Solution:** Enable `web_search_debug=true` to see detailed error logs

### Code Interpreter Issues

**Problem:** Code doesn't execute
- **Solution:** Make sure OpenWebUI has code interpreter feature enabled

**Problem:** Import errors in Jupyter mode
- **Solution:** Install required packages in your OpenWebUI environment

### Image Generation Issues

**Problem:** "Image generation failed: model not found"
- **Solution:** Check that `image_gen_model` is set to an available model

## Development

### Project Structure

```
master_tool/
├── agentic_master_tool.py  # Main tool implementation
├── README.md               # This file
└── examples/              # Example usage (optional)
```

### Dependencies

- `exa-py` >= 2.0.0 (for web search)
- OpenWebUI with code interpreter support
- Access to LLM models (OpenAI, Anthropic, etc.)

## Migration from Auto Tool Selector

If you're currently using the Auto Tool Selector, here's how to migrate:

1. **Install** the Agentic Master Tool alongside the old tool
2. **Test** in a new chat with an agentic model (GPT-4, Claude 3.5+)
3. **Compare** results - the master tool should give you more control
4. **Switch** by disabling Auto Tool Selector and enabling Agentic Master Tool
5. **Remove** the Auto Tool Selector once you're satisfied

## Contributing

Found a bug or want to add a feature? Contributions are welcome!

## License

MIT License - See project root for details

## Credits

- Web Search: Based on exa_router_search.py
- Code Interpreter: Inspired by OpenWebUI's code interpreter
- Image Generation: Uses OpenWebUI's image generation capabilities

---

**Version:** 1.0.0
**Author:** ShaoRou459
**Repository:** https://github.com/ShaoRou459/OpenWebUI-Agentic-Tooling
