"""
Title: URL Content Crawler
Description: Crawl and extract content from a specific URL using Exa
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 1.1.0
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

# Import universal debug system
try:
    from universal_debug import UniversalDebug, retry_async
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False
    # Fallback debug class
    class UniversalDebug:
        def __init__(self, *args, **kwargs): pass
        def __getattr__(self, name): return lambda *args, **kwargs: None

# URL pattern for extracting URLs from text
URL_RE = re.compile(r"https?://\S+")


class Tools:
    """URL Content Crawler Tool for OpenWebUI"""

    class Valves(BaseModel):
        exa_api_key: str = Field(
            default="",
            description="Your Exa API key for crawling URLs."
        )
        debug_enabled: bool = Field(
            default=False,
            description="Enable detailed debug logging."
        )
        max_retries: int = Field(
            default=3,
            description="Maximum number of retry attempts for failed operations."
        )
        retry_delay: float = Field(
            default=1.0,
            description="Initial delay in seconds before retrying failed operations."
        )

    def __init__(self):
        self.valves = self.Valves()
        self._exa: Optional[Exa] = None
        self.debug = UniversalDebug(enabled=False, tool_name="CrawlURL")

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

            with self.debug.timer("exa_client_init"):
                self._exa = Exa(key)
                self.debug.success("Exa client initialized")

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
        # Update debug state
        self.debug.enabled = self.valves.debug_enabled

        if self.debug.enabled:
            self.debug.start_session(f"Crawl URL: {url[:50]}...")

        # Check if Exa is available
        if not EXA_AVAILABLE:
            error_msg = "❌ URL crawler unavailable: exa_py module not installed. Please install with: pip install exa_py"
            self.debug.error("exa_py not available")
            return error_msg

        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        # Validate URL format
        if not url or not URL_RE.match(url):
            self.debug.error(f"Invalid URL: {url}")
            return "❌ Invalid URL provided. Please provide a valid HTTP/HTTPS URL."

        self.debug.info(f"Validating URL: {url}")
        await _status(f"Reading content from {url}...")

        try:
            exa = self._exa_client()

            self.debug.info(f"Starting crawl for: {url}")

            # Crawl the URL with retry logic
            async def _crawl():
                with self.debug.timer("exa_crawl"):
                    return await asyncio.to_thread(exa.get_contents, [url])

            crawled_results = await retry_async(
                _crawl,
                max_retries=self.valves.max_retries,
                initial_delay=self.valves.retry_delay,
                debug=self.debug,
                operation_name="URL crawl"
            )

            if not crawled_results.results:
                await _status("Crawl complete.", done=True)
                self.debug.warning("No results returned from crawl")
                if self.debug.enabled:
                    self.debug.metrics_summary()
                return "❌ Could not retrieve any content from the URL. The page might be empty or inaccessible."

            content = crawled_results.results[0].text

            if not content or not content.strip():
                await _status("Crawl complete.", done=True)
                self.debug.warning("Empty content retrieved")
                if self.debug.enabled:
                    self.debug.metrics_summary()
                return "❌ No text content found at the URL."

            # Track metrics
            self.debug.metrics.urls_crawled = 1
            self.debug.metrics.urls_successful = 1
            self.debug.metrics.total_content_chars = len(content)

            await _status("✓ Content extracted successfully", done=True)
            self.debug.success(f"Crawl successful: {len(content)} characters extracted")

            if self.debug.enabled:
                self.debug.metrics_summary()

            # Return the content with a header
            return f"# Content from {url}\n\n{content}"

        except Exception as e:
            await _status("", done=True)
            self.debug.error(f"Crawl failed: {str(e)}")
            self.debug.metrics.urls_failed = 1

            if self.debug.enabled:
                self.debug.metrics_summary()

            return f"❌ Failed to crawl URL: {str(e)}"
