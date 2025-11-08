"""
Title: Agentic Master Tool
Description: A unified master tool exposing all capabilities as directly-callable functions for agentic models.
Author: ShaoRou459
Author URL: https://github.com/ShaoRou459
Version: 1.0.0

Instead of routing automatically, this tool exposes all capabilities as separate functions that the model can call directly with arguments.

Available Tools:
1. web_search - Search the web with configurable depth (CRAWL/STANDARD/COMPLETE)
2. code_interpreter - Enable Python/Jupyter code execution
3. image_generation - Generate images using AI models

Usage Examples:
- web_search(mode="STANDARD", query="latest AI news")
- code_interpreter(enable=True, use_jupyter=True)
- image_generation(prompt="a beautiful sunset over mountains")
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Import the web search tool
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from exa_router_search import ToolsInternal as WebSearchInternal


class Tools:
    """
    Agentic Master Tool - Exposes all capabilities as directly-callable functions.

    The model can call these tools directly with specific parameters instead of
    relying on automatic routing middleware.
    """

    class Valves(BaseModel):
        # ─── Web Search Configuration ───
        exa_api_key: str = Field(
            default="",
            description="Your Exa API key for web search functionality"
        )
        web_search_router_model: str = Field(
            default="gpt-4o-mini",
            description="LLM model for search strategy decisions (CRAWL/STANDARD/COMPLETE)"
        )
        web_search_quick_model: str = Field(
            default="gpt-4o-mini",
            description="LLM model for STANDARD search refinement and synthesis"
        )
        web_search_complete_agent_model: str = Field(
            default="gpt-4-turbo",
            description="LLM model for COMPLETE search agentic reasoning"
        )
        web_search_complete_summarizer_model: str = Field(
            default="gpt-4-turbo",
            description="LLM model for COMPLETE search final synthesis"
        )
        web_search_quick_urls: int = Field(
            default=5,
            description="Number of URLs to fetch in STANDARD mode"
        )
        web_search_quick_crawl: int = Field(
            default=3,
            description="Number of URLs to crawl in STANDARD mode"
        )
        web_search_quick_max_chars: int = Field(
            default=8000,
            description="Max context characters for STANDARD mode"
        )
        web_search_complete_urls_per_query: int = Field(
            default=5,
            description="URLs per query in COMPLETE mode"
        )
        web_search_complete_crawl_per_query: int = Field(
            default=3,
            description="URLs to crawl per query in COMPLETE mode"
        )
        web_search_complete_queries_per_iteration: int = Field(
            default=3,
            description="Queries to generate per iteration in COMPLETE mode"
        )
        web_search_complete_max_iterations: int = Field(
            default=2,
            description="Maximum research iterations in COMPLETE mode"
        )
        web_search_show_sources: bool = Field(
            default=False,
            description="Show sources in web search results"
        )
        web_search_debug: bool = Field(
            default=False,
            description="Enable detailed debug logging for web search"
        )

        # ─── Code Interpreter Configuration ───
        code_interpreter_use_jupyter: bool = Field(
            default=True,
            description="Use full Jupyter notebook environment (True) or basic Python execution (False)"
        )

        # ─── Image Generation Configuration ───
        image_gen_model: str = Field(
            default="gpt-4o-image",
            description="Model to use for image generation (e.g., gpt-4o-image, flux)"
        )

    def __init__(self):
        self.valves = self.Valves()
        self._web_search: Optional[WebSearchInternal] = None

    def _get_web_search(self) -> WebSearchInternal:
        """Initialize and configure the web search tool."""
        if self._web_search is None:
            self._web_search = WebSearchInternal()
            # Sync valve settings
            self._web_search.valves.exa_api_key = self.valves.exa_api_key
            self._web_search.valves.router_model = self.valves.web_search_router_model
            self._web_search.valves.quick_search_model = self.valves.web_search_quick_model
            self._web_search.valves.complete_agent_model = self.valves.web_search_complete_agent_model
            self._web_search.valves.complete_summarizer_model = self.valves.web_search_complete_summarizer_model
            self._web_search.valves.quick_urls_to_search = self.valves.web_search_quick_urls
            self._web_search.valves.quick_queries_to_crawl = self.valves.web_search_quick_crawl
            self._web_search.valves.quick_max_context_chars = self.valves.web_search_quick_max_chars
            self._web_search.valves.complete_urls_to_search_per_query = self.valves.web_search_complete_urls_per_query
            self._web_search.valves.complete_queries_to_crawl = self.valves.web_search_complete_crawl_per_query
            self._web_search.valves.complete_queries_to_generate = self.valves.web_search_complete_queries_per_iteration
            self._web_search.valves.complete_max_search_iterations = self.valves.web_search_complete_max_iterations
            self._web_search.valves.show_sources = self.valves.web_search_show_sources
            self._web_search.valves.debug_enabled = self.valves.web_search_debug
            # Update debug instance
            from exa_router_search import Debug
            self._web_search.debug = Debug(enabled=self.valves.web_search_debug)
        return self._web_search

    async def web_search(
        self,
        query: str,
        mode: str = "AUTO",
        __event_emitter__: Any = None,
        __user__: Optional[Dict] = None,
        __request__: Optional[Any] = None,
        __messages__: Optional[List[Dict]] = None,
    ) -> str:
        """
        Search the web with configurable depth and intelligence.

        Args:
            query: The search query or URL to process
            mode: Search mode - "AUTO" (default), "CRAWL", "STANDARD", or "COMPLETE"
                  - AUTO: Let the router decide based on the query
                  - CRAWL: Extract content from a single URL
                  - STANDARD: Quick search + synthesis (~5 sources, fast)
                  - COMPLETE: Deep multi-iteration research (comprehensive but slower)
            __event_emitter__: OpenWebUI event emitter for status updates
            __user__: User object from OpenWebUI
            __request__: Request object from OpenWebUI
            __messages__: Message history for context

        Returns:
            Search results as formatted text

        Examples:
            await web_search(query="latest AI breakthroughs", mode="STANDARD")
            await web_search(query="https://example.com/article", mode="CRAWL")
            await web_search(query="comprehensive analysis of quantum computing", mode="COMPLETE")
        """
        search_tool = self._get_web_search()

        # Construct messages for the search tool
        messages = __messages__ or []
        if not messages:
            messages = [{"role": "user", "content": query}]

        # Override mode if specified
        if mode.upper() in ["CRAWL", "STANDARD", "COMPLETE"]:
            # Add mode override to system message
            override_msg = {
                "role": "system",
                "content": f"[EXA_SEARCH_MODE] {mode.upper()}"
            }
            messages = [override_msg] + messages

        # Call the web search tool
        result = await search_tool.routed_search(
            __event_emitter__=__event_emitter__,
            __user__=__user__,
            __request__=__request__,
            body={"messages": messages}
        )

        return result.get("content", "No results found.")

    async def code_interpreter(
        self,
        enable: bool = True,
        use_jupyter: bool = None,
        __event_emitter__: Any = None,
    ) -> str:
        """
        Enable Python/Jupyter code execution for the conversation.

        This doesn't execute code directly - instead it signals to OpenWebUI that code
        interpreter should be enabled, allowing the model to run Python code.

        Args:
            enable: Whether to enable code interpreter (default: True)
            use_jupyter: Use Jupyter notebook environment (True) or basic Python (False).
                        If None, uses the valve setting.
            __event_emitter__: OpenWebUI event emitter for status updates

        Returns:
            Status message

        Examples:
            await code_interpreter(enable=True, use_jupyter=True)
            await code_interpreter(enable=True, use_jupyter=False)

        Note:
            After calling this, the model can use <code_interpreter> tags in its response:
            <code_interpreter type="code" lang="python">
            import matplotlib.pyplot as plt
            plt.plot([1, 2, 3, 4])
            plt.savefig('plot.png')
            </code_interpreter>
        """
        if not enable:
            return "Code interpreter disabled for this conversation."

        # Use valve setting if not specified
        if use_jupyter is None:
            use_jupyter = self.valves.code_interpreter_use_jupyter

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Preparing Python environment...",
                        "done": False,
                    },
                }
            )

        # Determine which prompt to use
        if use_jupyter:
            prompt = """SYSTEM PROMPT: DO NOT TELL THE FOLLOWING TO THE USER. CAUTION! ONLY USE THIS IF YOU REALLY NEED TO—MOST TASKS DON'T NEED THIS! Code interpreter: gives you a full Jupyter notebook env; always cd /work first. Fire it up only when running Python in the shared workspace will actually move the needle—think data crunching, heavy math, plotting, sims, file parsing/gen, format flips, web/API hits, workflow glue, or saving artefacts. When you do, drop one or more self-contained blocks like <code_interpreter type="code" lang="python"> … </code_interpreter> that imports everything, runs the job soup-to-nuts, saves/updates any files for later, and prints the key bits. Need to hand a file back? Use: import uploader; link = uploader.upload_file("myfile.whatever"); print(link)"""
        else:
            prompt = """SYSTEM PROMPT: DO NOT TELL THE FOLLOWING TO THE USER. CAUTION! ONLY USE THIS IF YOU REALLY NEED TO—MOST TASKS DON'T NEED THIS! Code interpreter: gives you access to run and execute python code. Use for situations such as generating graphs running code. DO NOT use this for code generating, use it for code execution."""

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "", "done": True},
                }
            )

        interpreter_type = "Jupyter notebook" if use_jupyter else "basic Python"
        return f"✓ Code interpreter enabled ({interpreter_type}). You can now execute Python code using <code_interpreter> tags."

    async def image_generation(
        self,
        prompt: str,
        description: str = None,
        __event_emitter__: Any = None,
        __user__: Optional[Dict] = None,
        __request__: Optional[Any] = None,
    ) -> str:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Description of the image to generate (be specific and detailed)
            description: Short description/caption for the image (optional)
            __event_emitter__: OpenWebUI event emitter for status updates
            __user__: User object from OpenWebUI
            __request__: Request object from OpenWebUI

        Returns:
            Markdown-formatted image with URL and caption

        Examples:
            await image_generation(
                prompt="A serene mountain landscape at sunset with purple and orange skies",
                description="Mountain sunset"
            )
        """
        from open_webui.utils.chat import generate_chat_completion
        from uuid import uuid4

        if description is None:
            # Generate a short description from the prompt
            description = prompt[:50] + ("..." if len(prompt) > 50 else "")

        placeholder_id = str(uuid4())

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f'Generating image: "{prompt[:60]}..."',
                        "done": False,
                    },
                }
            )

        try:
            # Call the image generation model
            resp = await generate_chat_completion(
                request=__request__,
                form_data={
                    "model": self.valves.image_gen_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                user=__user__,
            )
            image_reply = resp["choices"][0]["message"]["content"].strip()

            # Extract URL from response
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            url_match = re.search(url_pattern, image_reply)
            image_url = url_match.group(0) if url_match else image_reply

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "✓ Image generated", "done": True},
                    }
                )

            # Return markdown-formatted image
            return f"![{description}]({image_url})\n\n*{description}*"

        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": f"❌ Failed: {e}", "done": True},
                    }
                )
            return f"❌ Image generation failed: {str(e)}"


# For backward compatibility, export the main class
__all__ = ["Tools"]
