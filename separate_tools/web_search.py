"""
Title: Web Search Tool
Description: Quick web search with multiple sources (STANDARD mode - no internal query refinement)
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 1.1.0
Requirements: exa_py, open_webui
"""

import os
import asyncio
from typing import Any, Callable, Awaitable, Dict, List, Optional
from urllib.parse import urlparse
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


class Tools:
    """Web Search Tool for OpenWebUI - optimized for AI model consumption"""

    class Valves(BaseModel):
        exa_api_key: str = Field(
            default="",
            description="Your Exa API key for web search."
        )
        urls_to_search: int = Field(
            default=5,
            description="Number of URLs to fetch from search results."
        )
        urls_to_crawl: int = Field(
            default=3,
            description="Number of top URLs to crawl for content."
        )
        max_content_chars: int = Field(
            default=12000,
            description="Maximum total characters of content to return."
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
        self.debug = UniversalDebug(enabled=False, tool_name="WebSearch")

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

    async def web_search(
        self,
        query: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
    ) -> str:
        """
        Search the web and return structured information from multiple sources.

        IMPORTANT: The calling AI model should provide an optimized search query.
        This tool does NOT refine the query - it uses exactly what you provide.

        Args:
            query: The search query (should be optimized by the calling model)
            __event_emitter__: OpenWebUI event emitter for status updates
            __request__: Request object from OpenWebUI
            __user__: User object from OpenWebUI

        Returns:
            Structured information from multiple web sources, formatted for AI consumption

        Examples:
            # Good query (optimized by calling model):
            await web_search("latest AI developments 2025")

            # Bad query (not optimized):
            await web_search("what's happening with AI?")
        """
        # Update debug state
        self.debug.enabled = self.valves.debug_enabled

        if self.debug.enabled:
            self.debug.start_session(f"Web search: {query[:50]}...")

        # Check if Exa is available
        if not EXA_AVAILABLE:
            error_msg = "❌ Web search unavailable: exa_py module not installed. Please install with: pip install exa_py"
            self.debug.error("exa_py not available")
            return error_msg

        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        if not query or not query.strip():
            self.debug.error("Empty query provided")
            return "❌ Empty search query provided. Please provide a valid search query."

        self.debug.info(f"Search query: {query}")

        try:
            exa = self._exa_client()

            # Step 1: Search with retry logic
            await _status(f'Searching for: "{query}"')
            self.debug.search(f"Executing search: {query}")

            async def _search():
                with self.debug.timer("exa_search"):
                    return await asyncio.to_thread(
                        exa.search,
                        query,
                        num_results=self.valves.urls_to_search
                    )

            search_results = await retry_async(
                _search,
                max_retries=self.valves.max_retries,
                initial_delay=self.valves.retry_delay,
                debug=self.debug,
                operation_name="web search"
            )

            if not search_results.results:
                await _status("", done=True)
                self.debug.warning("No search results found")
                if self.debug.enabled:
                    self.debug.metrics_summary()
                return f"❌ No search results found for query: {query}"

            self.debug.success(f"Found {len(search_results.results)} search results")
            self.debug.metrics.urls_found = len(search_results.results)

            # Step 2: Crawl top results
            crawl_candidates = search_results.results[:self.valves.urls_to_crawl]

            domains = [
                urlparse(res.url).netloc.replace("www.", "")
                for res in crawl_candidates
            ]

            await _status(f"Reading content from: {', '.join(domains)}")
            self.debug.info(f"Crawling {len(crawl_candidates)} URLs from: {', '.join(domains)}")

            ids_to_crawl = [res.id for res in crawl_candidates]

            async def _crawl():
                with self.debug.timer("exa_crawl"):
                    return await asyncio.to_thread(
                        exa.get_contents,
                        ids_to_crawl
                    )

            crawled_results = await retry_async(
                _crawl,
                max_retries=self.valves.max_retries,
                initial_delay=self.valves.retry_delay,
                debug=self.debug,
                operation_name="content crawl"
            )

            if not crawled_results.results:
                await _status("", done=True)
                self.debug.warning("No content retrieved from crawl")
                if self.debug.enabled:
                    self.debug.metrics_summary()
                return f"❌ Found {len(search_results.results)} search results but could not retrieve content from any of them."

            self.debug.success(f"Crawled {len(crawled_results.results)} sources successfully")
            self.debug.metrics.urls_crawled = len(ids_to_crawl)
            self.debug.metrics.urls_successful = len(crawled_results.results)

            # Step 3: Format results for AI consumption
            await _status("Formatting results...")
            self.debug.info("Formatting results for AI consumption")

            # Build structured response
            sources_data = []
            total_chars = 0

            for idx, result in enumerate(crawled_results.results, 1):
                if not result.text or not result.text.strip():
                    self.debug.warning(f"Empty content from source {idx}")
                    continue

                # Extract source info
                source_info = {
                    "number": idx,
                    "url": result.url,
                    "title": getattr(result, "title", "Untitled"),
                    "domain": urlparse(result.url).netloc.replace("www.", ""),
                    "text": result.text
                }

                sources_data.append(source_info)
                total_chars += len(result.text)

                # Stop if we've exceeded max chars
                if total_chars >= self.valves.max_content_chars:
                    self.debug.info(f"Reached max content limit ({self.valves.max_content_chars} chars)")
                    break

            if not sources_data:
                await _status("", done=True)
                self.debug.warning("All sources had empty content")
                if self.debug.enabled:
                    self.debug.metrics_summary()
                return f"❌ Retrieved {len(crawled_results.results)} sources but all had empty content."

            self.debug.metrics.total_content_chars = total_chars

            # Format as structured markdown for AI model
            formatted_output = self._format_for_ai(query, sources_data, total_chars)

            await _status("✓ Search complete", done=True)
            self.debug.success(f"Search complete: {len(sources_data)} sources, {total_chars} chars")

            if self.debug.enabled:
                self.debug.metrics_summary()

            return formatted_output

        except Exception as e:
            await _status("", done=True)
            self.debug.error(f"Web search failed: {str(e)}")

            if self.debug.enabled:
                self.debug.metrics_summary()

            return f"❌ Web search failed: {str(e)}"

    def _format_for_ai(self, query: str, sources: List[Dict], total_chars: int) -> str:
        """
        Format search results in a structured way optimized for AI model consumption.

        The format provides:
        - Clear metadata about the search
        - Structured source information
        - Full content for the AI to analyze
        """
        lines = [
            "# Web Search Results",
            f"**Query:** {query}",
            f"**Sources Retrieved:** {len(sources)}",
            f"**Total Content:** ~{total_chars:,} characters",
            "",
            "---",
            ""
        ]

        for source in sources:
            lines.extend([
                f"## Source {source['number']}: {source['title']}",
                f"**URL:** {source['url']}",
                f"**Domain:** {source['domain']}",
                "",
                "**Content:**",
                "",
                source['text'],
                "",
                "---",
                ""
            ])

        lines.extend([
            "",
            "**Instructions for AI Model:**",
            "- Analyze the above sources to answer the user's question",
            "- Synthesize information across multiple sources when relevant",
            "- Cite specific sources when making claims (e.g., 'According to Source 1...')",
            "- If sources conflict, acknowledge different perspectives",
            "- Focus on the most relevant and recent information",
            ""
        ])

        return "\n".join(lines)
