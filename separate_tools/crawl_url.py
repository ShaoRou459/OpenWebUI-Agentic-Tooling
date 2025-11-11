"""
Title: URL Content Crawler
Description: Crawl and extract content from a specific URL using Exa
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 1.0.0
Requirements: exa_py, open_webui
"""

import os
import re
import asyncio
from typing import Any, Callable, Awaitable, Dict, Optional
from pydantic import BaseModel, Field

try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    Exa = None
    EXA_AVAILABLE = False

# URL pattern for extracting URLs from text
URL_RE = re.compile(r"https?://\S+")


class Tools:
    """URL Content Crawler Tool for OpenWebUI"""

    class Valves(BaseModel):
        exa_api_key: str = Field(
            default="",
            description="Your Exa API key for crawling URLs."
        )

    def __init__(self):
        self.valves = self.Valves()
        self._exa: Optional[Exa] = None

    def _exa_client(self) -> Exa:
        """Initialize and return Exa client."""
        if self._exa is None:
            if Exa is None:
                raise RuntimeError(
                    "exa_py not installed. Please install with: pip install exa_py"
                )
            key = self.valves.exa_api_key or os.getenv("EXA_API_KEY")
            if not key:
                raise RuntimeError(
                    "Exa API key missing. Please set exa_api_key in valves or EXA_API_KEY environment variable"
                )
            self._exa = Exa(key)
        return self._exa

    async def crawl_url(
        self,
        url: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
    ) -> str:
        """
        Crawl and extract content from a specific URL.

        Args:
            url: The URL to crawl and extract content from
            __event_emitter__: OpenWebUI event emitter for status updates
            __request__: Request object from OpenWebUI
            __user__: User object from OpenWebUI

        Returns:
            The extracted text content from the URL

        Examples:
            await crawl_url("https://example.com/article")
        """
        # Check if Exa is available
        if not EXA_AVAILABLE:
            error_msg = "❌ URL crawler unavailable: exa_py module not installed. Please install with: pip install exa_py"
            return error_msg

        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        # Validate URL format
        if not url or not URL_RE.match(url):
            return "❌ Invalid URL provided. Please provide a valid HTTP/HTTPS URL."

        await _status(f"Reading content from {url}...")

        try:
            exa = self._exa_client()

            # Crawl the URL
            crawled_results = await asyncio.to_thread(exa.get_contents, [url])

            if not crawled_results.results:
                await _status("Crawl complete.", done=True)
                return "❌ Could not retrieve any content from the URL. The page might be empty or inaccessible."

            content = crawled_results.results[0].text

            if not content or not content.strip():
                await _status("Crawl complete.", done=True)
                return "❌ No text content found at the URL."

            await _status("✓ Content extracted successfully", done=True)

            # Return the content with a header
            return f"# Content from {url}\n\n{content}"

        except Exception as e:
            await _status("", done=True)
            return f"❌ Failed to crawl URL: {str(e)}"
