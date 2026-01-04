"""
Title: Exa Agentic Search Tool
Description: An intelligent agentic research tool with full control over Exa search parameters.
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 2.0.0
Requirements: exa_py, open_webui
"""

from __future__ import annotations

import os
import re
import sys
import json
import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from open_webui.utils.misc import get_last_user_message

try:
    from exa_py import Exa

    EXA_AVAILABLE = True
except ImportError:
    Exa = None
    EXA_AVAILABLE = False


# ─── System Prompts ───────────────────────────────────────────────────────────

AGENTIC_SEARCH_PROMPT = """
You are an intelligent web search agent. Your job is to search for information on the web efficiently and effectively based on the user's request. 

CURRENT DATE: {current_date}
USER REQUEST: {user_request}
SOURCES CONSULTED: {source_count}

{previous_findings}

{new_content_section}

---

## SEARCH PARAMETER OPTIONS (for SEARCH_CONFIG):

**search_type**: "auto" (default), "neural" (semantic), "fast" (speed), "deep" (comprehensive)
**category**: null, "news", "research paper", "github", "company", "people", "tweet", "pdf", "personal site", "financial report"
**num_results**: 1-25 (default 10)
**start_published_date** / **end_published_date**: "YYYY-MM-DD" or null
**include_domains** / **exclude_domains**: ["domain.com"] or null
**include_text**: "required phrase" or null (max 5 words)

---

## DECISION GUIDELINES:

This is where you decide whether to continue searching or not. The important rule is to be sensible; make sure you do not over/under search. Interpret the user's expectations based on their request. Time is money.

**STOP** when: You have sufficient information, simple queries answered, or more searching would be redundant.

**CONTINUE** when: Results are incomplete, query is complex/research-oriented, or key aspects are missing.

---

## OUTPUT FORMAT (ALWAYS use this exact structure, in this order):

EXTRACTED_INFO:
<Key facts extracted from new content. Write "None - no content yet" if this is the first iteration.>

EVALUATION:
<Brief assessment: What do we have? Is it sufficient for this query?>

DECISION: STOP or CONTINUE

SEARCH_CONFIG:
```json
{{
  "search_type": "auto",
  "category": null,
  "num_results": 10,
  "start_published_date": null,
  "end_published_date": null,
  "include_domains": null,
  "exclude_domains": null,
  "include_text": null,
  "queries": ["search query"]
}}
```
<If DECISION is STOP, use empty queries: {{"queries": []}}. If CONTINUE, provide optimized queries.>

RESEARCH_SUMMARY:
<If DECISION is STOP: Provide a well-organized summary of ALL findings for the chat model to use.>
<If DECISION is CONTINUE: Write "Continuing search...">

KEY_POINTS:
<If DECISION is STOP: List the most important findings as bullet points.>
<If DECISION is CONTINUE: Write "N/A">
"""


# ─── Enhanced Debug System ──────────────────────────────────────────────────
from contextlib import contextmanager

@dataclass
class IterationRecord:
    """Record of a single search iteration."""
    iteration_num: int
    query: str
    search_type: str
    category: Optional[str]
    num_results: int
    results_found: int
    decision: str
    duration: float = 0.0


@dataclass
class DebugMetrics:
    """Collects and tracks metrics throughout the debug session."""
    
    # Timing
    start_time: float = field(default_factory=time.perf_counter)
    
    # Iteration tracking
    iterations: List[IterationRecord] = field(default_factory=list)
    
    # Totals
    total_sources: int = 0
    llm_calls: int = 0
    llm_total_time: float = 0.0
    
    # Issues
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_total_time(self) -> float:
        return time.perf_counter() - self.start_time


class Debug:
    """Clean, focused debug logging for AgenticSearchTool."""

    C = {"R": "\x1b[0m", "B": "\x1b[1m", "D": "\x1b[2m", "CY": "\x1b[96m", "GR": "\x1b[92m", 
         "YE": "\x1b[93m", "RD": "\x1b[91m", "MG": "\x1b[95m", "BL": "\x1b[94m", "WH": "\x1b[97m"}

    def __init__(self, enabled: bool = False, tool_name: str = "AgenticSearch"):
        self.enabled = enabled
        self.tool_name = tool_name
        self.metrics = DebugMetrics()
        self._session_id = str(int(time.time()))[-4:]
        self._current_iter: Optional[IterationRecord] = None
        self._iter_start: float = 0

    def _print(self, msg: str) -> None:
        if self.enabled:
            print(msg, file=sys.stderr)

    def start_session(self, query: str = "") -> None:
        self.metrics = DebugMetrics()
        if not self.enabled:
            return
        self._print(f"\n{self.C['MG']}{'═' * 60}{self.C['R']}")
        self._print(f"{self.C['B']}{self.C['MG']}  🔍 AGENTIC SEARCH [{self._session_id}]{self.C['R']}")
        self._print(f"{self.C['MG']}{'═' * 60}{self.C['R']}")
        if query:
            self._print(f"{self.C['D']}  Query: {query[:70]}{'...' if len(query) > 70 else ''}{self.C['R']}")

    def start_iteration(self, iteration: int, max_iter: int) -> None:
        self._iter_start = time.perf_counter()
        if self.enabled:
            self._print(f"\n{self.C['B']}{self.C['BL']}▶ ITERATION {iteration}/{max_iter}{self.C['R']}")

    def search_config(self, config: Dict[str, Any]) -> None:
        query = config.get("queries", ["N/A"])[0] if config.get("queries") else "N/A"
        search_type = config.get("search_type", "auto")
        category = config.get("category") or "any"
        num_results = config.get("num_results", 10)
        self._current_iter = IterationRecord(len(self.metrics.iterations) + 1, query[:50], search_type, category, num_results, 0, "PENDING")
        if not self.enabled:
            return
        self._print(f"  {self.C['D']}├─{self.C['R']} {self.C['GR']}Config:{self.C['R']}")
        self._print(f"  {self.C['D']}│{self.C['R']}   Query: {self.C['WH']}{query[:50]}{'...' if len(query) > 50 else ''}{self.C['R']}")
        self._print(f"  {self.C['D']}│{self.C['R']}   Type: {self.C['CY']}{search_type}{self.C['R']} | Cat: {self.C['CY']}{category}{self.C['R']} | Num: {self.C['CY']}{num_results}{self.C['R']}")

    def search_results(self, count: int) -> None:
        if self._current_iter:
            self._current_iter.results_found = count
            self.metrics.total_sources += count
        if self.enabled:
            self._print(f"  {self.C['D']}├─{self.C['R']} {self.C['GR']}Results: {count} docs{self.C['R']}")

    def sources_found(self, sources: List[Dict[str, str]]) -> None:
        """Show the top sources found in this iteration."""
        if not self.enabled or not sources:
            return
        for src in sources[:4]:  # Show top 4
            domain = src.get("url", "").split('/')[2] if '/' in src.get("url", "") else "unknown"
            title = src.get("title", "Untitled")[:40]
            self._print(f"  {self.C['D']}│{self.C['R']}     • {self.C['CY']}{domain}{self.C['R']} - {title}{'...' if len(src.get('title', '')) > 40 else ''}")

    def agent_evaluation(self, evaluation: str) -> None:
        """Show the agent's full evaluation/reasoning."""
        if not self.enabled or not evaluation:
            return
        self._print(f"  {self.C['D']}│{self.C['R']}   {self.C['MG']}Eval:{self.C['R']}")
        # Show each line of the evaluation
        for line in evaluation.strip().split('\n'):
            line = line.strip()
            if line:
                self._print(f"  {self.C['D']}│{self.C['R']}     {self.C['MG']}{line}{self.C['R']}")

    def agent_decision(self, decision: str, reason: str = "") -> None:
        if self._current_iter:
            self._current_iter.decision = decision
            self._current_iter.duration = time.perf_counter() - self._iter_start
            self.metrics.iterations.append(self._current_iter)
            self._current_iter = None
        if self.enabled:
            color = self.C['GR'] if decision == "STOP" else self.C['YE']
            symbol = "✓" if decision == "STOP" else "→"
            self._print(f"  {self.C['D']}└─{self.C['R']} {color}{self.C['B']}Decision: {symbol} {decision}{self.C['R']}")

    def llm_call(self, model: str, success: bool = True, duration: float = 0.0) -> None:
        self.metrics.llm_calls += 1
        self.metrics.llm_total_time += duration
        if self.enabled and duration > 0:
            self._print(f"  {self.C['D']}│{self.C['R']}   {self.C['GR'] if success else self.C['RD']}{'✓' if success else '✗'} LLM ({duration:.2f}s){self.C['R']}")

    def error(self, message: str) -> None:
        self.metrics.errors.append(message[:200])  # Truncate for summary
        # Errors shown in summary to keep iteration flow clean

    def warning(self, message: str) -> None:
        self.metrics.warnings.append(message)
        # Only tracks, doesn't print - shown in summary

    def flow(self, message: str) -> None:
        pass  # Silent - key info captured by specialized methods

    def synthesis(self, message: str) -> None:
        pass  # Silent - summary shown in metrics_summary

    # Legacy compatibility methods (minimal/silent)
    def data(self, label: str, data: Any, truncate: int = 100) -> None:
        pass
    def iteration(self, message: str) -> None:
        pass
    def agent(self, message: str) -> None:
        pass
    def search(self, message: str) -> None:
        pass
    def url_metrics(self, found: int = 0, crawled: int = 0, successful: int = 0, failed: int = 0) -> None:
        self.metrics.total_sources += successful
    def content_metrics(self, chars: int, truncated: bool = False) -> None:
        pass
    def report(self, message: str) -> None:
        pass
    @contextmanager
    def timer(self, operation_name: str):
        yield

    def metrics_summary(self) -> None:
        if not self.enabled:
            return
        total_time = self.metrics.get_total_time()
        self._print(f"\n{self.C['MG']}{'═' * 60}{self.C['R']}")
        self._print(f"{self.C['B']}{self.C['MG']}  📊 SESSION SUMMARY{self.C['R']}")
        self._print(f"{self.C['MG']}{'═' * 60}{self.C['R']}")
        if self.metrics.iterations:
            self._print(f"\n  {self.C['B']}Iterations:{self.C['R']}")
            for it in self.metrics.iterations:
                dec_color = self.C['GR'] if it.decision == "STOP" else self.C['YE']
                self._print(f"  {self.C['B']}#{it.iteration_num}{self.C['R']} {it.search_type:6} | {it.results_found:2} docs | {dec_color}{'✓' if it.decision == 'STOP' else '→'}{it.decision}{self.C['R']} | {it.duration:.1f}s")
                self._print(f"     {self.C['D']}└ {it.query}{self.C['R']}")
        self._print(f"\n  {self.C['B']}Stats:{self.C['R']} {total_time:.1f}s total | {self.metrics.llm_calls} LLM calls | {self.metrics.total_sources} sources")
        
        # Show errors/warnings at the end
        if self.metrics.errors:
            self._print(f"\n  {self.C['RD']}{self.C['B']}Errors ({len(self.metrics.errors)}):{self.C['R']}")
            for err in self.metrics.errors[:3]:  # Show up to 3
                self._print(f"    {self.C['RD']}• {err[:80]}{'...' if len(err) > 80 else ''}{self.C['R']}")
        if self.metrics.warnings:
            self._print(f"\n  {self.C['YE']}Warnings ({len(self.metrics.warnings)}):{self.C['R']}")
            for warn in self.metrics.warnings[:3]:
                self._print(f"    {self.C['YE']}• {warn[:80]}{self.C['R']}")
        
        self._print(f"\n{self.C['MG']}{'═' * 60}{self.C['R']}\n")


# ─── Constants & Helpers ──────────────────────────────────────────────────────
URL_RE = re.compile(r"https?://\S+")


def _get_text_from_message(message_content: Any) -> str:
    """Extracts only the text part of a message, ignoring image data URLs."""
    if isinstance(message_content, list):
        text_parts = []
        for part in message_content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return " ".join(text_parts)
    elif isinstance(message_content, str):
        return message_content
    return ""


async def generate_with_retry(
    max_retries: int = 3, delay: int = 3, debug: Debug = None, **kwargs: Any
) -> Dict[str, Any]:
    """
    A wrapper for generate_chat_completion that includes a retry mechanism with exponential backoff.
    """
    def _normalize_llm_response(res: Any) -> Dict[str, Any]:
        # Already a dict
        if isinstance(res, dict):
            return res
        
        # Debug what we actually got
        if debug:
            debug.error(f"LLM response normalization needed. Type: {type(res)}, Dir: {[attr for attr in dir(res) if not attr.startswith('_')]}")
        
        # If it's a JSONResponse (Starlette/FastAPI), extract the body and parse
        try:
            if hasattr(res, 'body') and hasattr(res, 'status_code'):
                import json
                body_bytes = res.body
                if isinstance(body_bytes, bytes):
                    parsed = json.loads(body_bytes.decode('utf-8'))
                    if debug:
                        debug.flow(f"Successfully parsed JSONResponse body")
                        debug.data("Full parsed response", str(parsed)[:500] + "..." if len(str(parsed)) > 500 else str(parsed))
                        debug.data("Response keys", list(parsed.keys()) if isinstance(parsed, dict) else "Not a dict")
                    return parsed
                elif isinstance(body_bytes, str):
                    parsed = json.loads(body_bytes)
                    if debug:
                        debug.flow(f"Successfully parsed JSONResponse string body")
                        debug.data("Full parsed response", str(parsed)[:500] + "..." if len(str(parsed)) > 500 else str(parsed))
                        debug.data("Response keys", list(parsed.keys()) if isinstance(parsed, dict) else "Not a dict")
                    return parsed
        except Exception as e:
            if debug:
                debug.error(f"Failed to parse JSONResponse body: {e}")
        
        # Try to call render() method if available (for Response objects)
        try:
            if hasattr(res, 'render'):
                import json
                rendered = res.render(None)  # Pass None as scope if not needed
                if isinstance(rendered, bytes):
                    parsed = json.loads(rendered.decode('utf-8'))
                    if debug:
                        debug.flow(f"Successfully parsed rendered response")
                    return parsed
        except Exception as e:
            if debug:
                debug.error(f"Failed to render and parse response: {e}")
        
        # Check if it's already JSON-like but not a dict
        try:
            if hasattr(res, '__dict__'):
                return res.__dict__
        except Exception:
            pass
            
        # Last resort: if it has a dict-like interface
        try:
            return dict(res)  # may raise
        except Exception as e:
            if debug:
                debug.error(f"Failed to convert to dict: {e}")
            raise TypeError(f"LLM response is not a dict and could not be normalized. Type: {type(res)}, Value: {str(res)[:200]}")

    model_name = kwargs.get('form_data', {}).get('model', 'unknown')
    last_exception = None
    
    for attempt in range(max_retries):
        start_time = time.perf_counter()
        try:
            raw = await generate_chat_completion(**kwargs)
            result = _normalize_llm_response(raw)
            duration = time.perf_counter() - start_time
            
            if debug:
                debug.llm_call(model_name, success=True, duration=duration)
                if attempt > 0:
                    debug.flow(f"LLM call succeeded on attempt {attempt + 1}")
            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            last_exception = e
            
            if debug:
                debug.llm_call(model_name, success=False, duration=duration)
                debug.error(
                    f"LLM call failed on attempt {attempt + 1}/{max_retries}: {str(e)[:100]}..."
                )

            # Don't wait on the last attempt
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = delay * (2**attempt) + (attempt * 0.5)
                await asyncio.sleep(wait_time)

    if debug:
        debug.error(
            f"LLM call failed after {max_retries} retries. Last error: {str(last_exception)[:100]}..."
        )
    raise last_exception


async def generate_with_parsing_retry(
    max_retries: int = 3, delay: int = 3, debug: Debug = None, 
    expected_keys: List[str] = None, **kwargs: Any
) -> Dict[str, Any]:
    """
    A wrapper that combines generate_with_retry with parsing retry logic.
    Retries both API failures and response parsing failures.
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # First, try the API call with retry
            result = await generate_with_retry(max_retries=max_retries, delay=delay, debug=debug, **kwargs)
            
            # Then validate the response format
            if expected_keys:
                if isinstance(result, dict):
                    # Check if any expected key exists
                    if any(key in result for key in expected_keys):
                        return result
                    else:
                        # Log the parsing issue and retry
                        if debug:
                            debug.warning(f"Response missing expected keys {expected_keys}. Got keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}. Attempt {attempt + 1}/{max_retries}")
                        raise ValueError(f"Response missing expected keys {expected_keys}. Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                else:
                    if debug:
                        debug.warning(f"Response is not a dict. Type: {type(result)}. Attempt {attempt + 1}/{max_retries}")
                    raise ValueError(f"Response is not a dict. Type: {type(result)}")
            else:
                # No specific validation needed, return result
                return result
                
        except Exception as e:
            last_exception = e
            
            if debug:
                debug.error(f"Generate with parsing retry failed on attempt {attempt + 1}/{max_retries}: {str(e)[:100]}...")
            
            # Don't wait on the last attempt
            if attempt < max_retries - 1:
                # Use same exponential backoff as generate_with_retry
                wait_time = delay * (2**attempt) + (attempt * 0.5)
                if debug:
                    debug.flow(f"Waiting {wait_time:.1f}s before retry attempt {attempt + 2}")
                await asyncio.sleep(wait_time)
    
    if debug:
        debug.error(f"Generate with parsing retry failed after {max_retries} retries. Last error: {str(last_exception)[:100]}...")
    raise last_exception


# ─── Core Tool Implementation ─────────────────────────────────────────────────
class ToolsInternal:

    class Valves(BaseModel):
        exa_api_key: str = Field(default="", description="Your Exa API key.")
        agent_model: str = Field(
            default="gpt-4o-mini",
            description="LLM model for the agentic search (extraction, evaluation, query generation).",
        )
        max_iterations: int = Field(
            default=3,
            description="Maximum number of search iterations before returning results.",
        )
        debug_enabled: bool = Field(
            default=False,
            description="Enable detailed debug logging for troubleshooting search operations.",
        )
        show_sources: bool = Field(
            default=False,
            description="If true, emit citation events so sources appear in the UI.",
        )

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.citation = False  # REQUIRED: Disable automatic citations so custom citation events work
        self.debug = Debug(enabled=False)  # Will be updated when valves change
        self._exa: Optional[Exa] = None
        self._query_cache: Dict[str, Any] = {}  # Simple query caching
        self._cache_max_size = 100  # Limit cache size
        self._active_sessions: Dict[str, asyncio.Lock] = {}  # Session concurrency control
        self._session_lock = asyncio.Lock()  # Lock for managing session locks
        self._last_error: Optional[str] = None  # Track the most recent error for user feedback

    def _exa_client(self) -> Exa:
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
            try:
                self._exa = Exa(key)
                self.debug.flow("🔑 Exa client initialised successfully")
            except Exception as e:
                self.debug.error(f"Failed to initialize Exa client: {e}")
                raise RuntimeError(f"Failed to initialize Exa client: {e}")
        return self._exa

    def _parse_search_config(self, agent_response: str) -> Dict[str, Any]:
        """
        Parse the agent's SEARCH_CONFIG JSON block from its response.
        Returns a validated config dict with defaults for missing values.
        """
        import re
        
        default_config = {
            "search_type": "auto",
            "category": None,
            "num_results": 10,
            "start_published_date": None,
            "end_published_date": None,
            "include_domains": None,
            "exclude_domains": None,
            "include_text": None,
            "queries": []
        }
        
        try:
            # Try to find JSON block in markdown code fence
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', agent_response, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group(1))
            else:
                # Try to find raw JSON object
                json_match = re.search(r'SEARCH_CONFIG:\s*(\{.*?\})', agent_response, re.DOTALL)
                if json_match:
                    config = json.loads(json_match.group(1))
                else:
                    # Last resort: find any JSON object
                    json_match = re.search(r'\{[^{}]*"queries"[^{}]*\}', agent_response, re.DOTALL)
                    if json_match:
                        config = json.loads(json_match.group(0))
                    else:
                        self.debug.warning("Could not find SEARCH_CONFIG JSON in agent response")
                        return default_config
            
            # Validate and sanitize the config
            validated = default_config.copy()
            
            # Search type
            if config.get("search_type") in ["auto", "neural", "fast", "deep"]:
                validated["search_type"] = config["search_type"]
            
            # Category
            valid_categories = [
                "news", "research paper", "github", "company", "people", 
                "tweet", "pdf", "personal site", "financial report"
            ]
            if config.get("category") in valid_categories:
                validated["category"] = config["category"]
            
            # Num results (1-25)
            if isinstance(config.get("num_results"), int):
                validated["num_results"] = max(1, min(25, config["num_results"]))
            
            # Date filters
            date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
            if config.get("start_published_date") and date_pattern.match(str(config["start_published_date"])):
                validated["start_published_date"] = config["start_published_date"]
            if config.get("end_published_date") and date_pattern.match(str(config["end_published_date"])):
                validated["end_published_date"] = config["end_published_date"]
            
            # Domain filters
            if isinstance(config.get("include_domains"), list):
                validated["include_domains"] = [d for d in config["include_domains"] if isinstance(d, str)]
            if isinstance(config.get("exclude_domains"), list):
                validated["exclude_domains"] = [d for d in config["exclude_domains"] if isinstance(d, str)]
            
            # Include text (max 5 words)
            if isinstance(config.get("include_text"), str):
                words = config["include_text"].split()
                if len(words) <= 5:
                    validated["include_text"] = config["include_text"]
            
            # Queries
            if isinstance(config.get("queries"), list):
                validated["queries"] = [q for q in config["queries"] if isinstance(q, str) and q.strip()]
            
            self.debug.flow(f"Parsed search config: {validated}")
            return validated
            
        except json.JSONDecodeError as e:
            self.debug.warning(f"JSON parse error in search config: {e}")
            return default_config
        except Exception as e:
            self.debug.error(f"Error parsing search config: {e}")
            return default_config

    async def _agentic_search_with_config(
        self, config: Dict[str, Any], debug_context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Execute Exa search using agent-determined parameters.
        Uses search_and_contents for efficiency (single API call).
        Returns list of results with text content included.
        """
        queries = config.get("queries", [])
        if not queries:
            self.debug.warning("No queries provided in search config")
            return []
        
        all_results = []
        
        with self.debug.timer(f"agentic_search_{debug_context}"):
            try:
                exa = self._exa_client()
                
                # Execute only the first query (one query per iteration)
                query = queries[0]
                self.debug.search(f"Executing query: {query[:60]}...")
                
                # Build search parameters - agent controls num_results (capped at Exa's max of 25)
                search_kwargs = {
                    "query": query,
                    "num_results": min(config.get("num_results", 10), 25),
                    "text": True,  # Include text content
                }
                
                # Add optional parameters
                if config.get("category"):
                    search_kwargs["category"] = config["category"]
                if config.get("start_published_date"):
                    search_kwargs["start_published_date"] = config["start_published_date"]
                if config.get("end_published_date"):
                    search_kwargs["end_published_date"] = config["end_published_date"]
                if config.get("include_domains"):
                    search_kwargs["include_domains"] = config["include_domains"]
                if config.get("exclude_domains"):
                    search_kwargs["exclude_domains"] = config["exclude_domains"]
                if config.get("include_text"):
                    search_kwargs["include_text"] = config["include_text"]
                
                # Map search type to Exa's use_autoprompt parameter
                search_type = config.get("search_type", "auto")
                if search_type == "neural":
                    search_kwargs["use_autoprompt"] = True
                elif search_type == "fast":
                    search_kwargs["use_autoprompt"] = False
                # "auto" and "deep" use default behavior
                
                result = await asyncio.to_thread(
                    exa.search_and_contents,
                    **search_kwargs
                )
                
                # Use all results since search_and_contents already returns text
                for r in result.results:
                    all_results.append({
                        "url": getattr(r, "url", ""),
                        "title": getattr(r, "title", ""),
                        "text": getattr(r, "text", ""),
                        "published_date": getattr(r, "published_date", None),
                    })
                
                self.debug.search(f"Query returned {len(result.results)} results with content")
                self.debug.url_metrics(found=len(result.results), successful=len(result.results))
                
                self.debug.flow(f"Total results collected: {len(all_results)}")
                return all_results
                
            except Exception as e:
                self.debug.error(f"Agentic search failed: {e}")
                return []

    def _extract_section(self, text: str, section_marker: str) -> str:
        """
        Extract multi-line content from a section that starts with section_marker.
        Stops when it hits another known section marker or end of text.
        """
        known_markers = [
            "EXTRACTED_INFO:", "EVALUATION:", "DECISION:", "SEARCH_CONFIG:",
            "RESEARCH_SUMMARY:", "KEY_POINTS:", "STATUS_SUMMARY:"
        ]
        
        lines = text.split("\n")
        capturing = False
        content_lines = []
        
        for line in lines:
            line_upper = line.upper().strip()
            
            # Check if this line starts our target section
            if section_marker.upper() in line_upper:
                capturing = True
                # Get any content after the marker on the same line
                after_marker = line.split(":", 1)
                if len(after_marker) > 1 and after_marker[1].strip():
                    content_lines.append(after_marker[1].strip())
                continue
            
            # Check if we hit a different section marker
            if capturing:
                hit_new_section = False
                for marker in known_markers:
                    if marker.upper() in line_upper and marker.upper() != section_marker.upper():
                        hit_new_section = True
                        break
                
                if hit_new_section:
                    break
                
                # Add this line to content
                content_lines.append(line)
        
        return "\n".join(content_lines).strip()

    def _get_session_lock(self, user_id: str, query_hash: str) -> asyncio.Lock:
        """Get or create a session lock for concurrent call protection."""
        session_key = f"{user_id}:{query_hash}"
        if session_key not in self._active_sessions:
            self._active_sessions[session_key] = asyncio.Lock()
        return self._active_sessions[session_key]

    async def _cleanup_session_lock(self, user_id: str, query_hash: str) -> None:
        """Clean up session lock after completion."""
        session_key = f"{user_id}:{query_hash}"
        async with self._session_lock:
            if session_key in self._active_sessions:
                del self._active_sessions[session_key]

    async def agentic_search(
        self,
        query: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
        __messages__: Optional[List[Dict]] = None,
        image_context: Optional[str] = None,
    ) -> dict:
        """Main entry point for agentic search."""
        # Guard: some environments may not have show_sources in valves
        show_sources = bool(getattr(self.valves, "show_sources", False))
        
        # Check if Exa is available first
        if not EXA_AVAILABLE:
            error_msg = "❌ Search tool unavailable: exa_py module not installed. Please install with: pip install exa_py"
            self.debug.error(error_msg)
            return {
                "content": error_msg,
            }

        # Generate session identifiers for concurrency control
        user_id = __user__.get("id", "unknown") if __user__ else "unknown"
        query_hash = str(hash(query))[-8:]  # Use last 8 chars of query hash
        
        # Get session lock to prevent concurrent calls
        session_lock = self._get_session_lock(user_id, query_hash)
        
        # Check if another instance is already running for this user/query combo
        if session_lock.locked():
            self.debug.flow(f"Concurrent call detected for user {user_id}, query hash {query_hash}")
            return {
                "content": "⚠️ A search is already in progress for this query. Please wait for it to complete before starting a new search.",
            }
        
        # Acquire the lock for this session
        async with session_lock:
            # Update debug state based on current valve setting
            self.debug.enabled = self.valves.debug_enabled
            if self.debug.enabled:
                self.debug.start_session(query)
            
            try:
                return await self._execute_agentic_search(
                    query, __event_emitter__, __request__, __user__, __messages__, image_context, show_sources
                )
            finally:
                # Clean up the session lock
                await self._cleanup_session_lock(user_id, query_hash)
                # Safety: ensure any transient status is cleared at the end
                if __event_emitter__:
                    try:
                        await __event_emitter__({
                            "type": "status",
                            "data": {"description": "", "done": True},
                        })
                    except Exception:
                        pass

    async def _execute_agentic_search(
        self,
        query: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
        __messages__: Optional[List[Dict]] = None,
        image_context: Optional[str] = None,
        show_sources: bool = False,
    ) -> dict:
        """Execute the agentic search with full agent control over search parameters."""

        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        # Add debug info about the tool being called
        self.debug.flow(f"AgenticSearch tool called with query: {query[:100]}...")
        if __user__:
            self.debug.data("User ID", __user__.get("id", "unknown"))
        if __messages__:
            self.debug.data("Message count", len(__messages__))

        messages = __messages__ or []
        last_user_message = get_last_user_message(messages)
        if not last_user_message:
            self.debug.error("Could not find a user message to process")
            return {
                "content": "Could not find a user message to process. Please try again.",
                "show_source": show_sources,
            }

        self.debug.data("Search query (from AI)", query)
        self.debug.data("Raw user message (for context)", last_user_message)

        # Build conversation history snippet for context
        history_messages = messages[-6:-1]
        convo_snippet_parts = []
        for m in history_messages:
            text_content = _get_text_from_message(m.get("content", ""))
            role = m.get("role", "").upper()
            convo_snippet_parts.append(f"{role}: {text_content!r}")
        convo_snippet = "\n".join(convo_snippet_parts)

        # Include image context if provided
        if image_context:
            self.debug.flow("Image context provided, enhancing search")
            convo_snippet += f"\n\nIMAGE CONTEXT: {image_context}"

        user_obj = Users.get_user_by_id(__user__["id"]) if __user__ else None
        
        # Start the agentic search
        self._last_error = None
        self.debug.flow("Starting agentic search with full parameter control")

        try:
            current_date = datetime.now().strftime("%Y-%m-%d")

            # Configuration
            max_iterations = self.valves.max_iterations

            all_findings = []
            all_sources = []  # List of {"url": ..., "title": ...} dicts for OpenWebUI
            iteration = 0
            final_agent_response = None
            
            # Initialize with default search config - agent will refine in first iteration
            search_config = {
                "search_type": "auto",
                "category": None,
                "num_results": 10,
                "queries": [query]
            }

            # ─── Iterative Search with Agent Control ─────────────────────────────────
            while iteration < max_iterations:
                iteration += 1
                self.debug.start_iteration(iteration, max_iterations)

                # Execute search with agent-determined parameters
                await _status(f"Searching ({search_config.get('search_type', 'auto')} mode)...")
                # Log the config being used for this iteration
                self.debug.search_config(search_config)
                
                search_results = await self._agentic_search_with_config(
                    search_config, 
                    f"iter_{iteration}"
                )

                # Format results for agent evaluation
                iteration_content = []
                for result in search_results:
                    if result.get("text"):
                        text = ' '.join(result["text"].split()[:1500])  # Truncate
                        url = result.get("url", "Unknown")
                        title = result.get("title", "Untitled")
                        iteration_content.append(f"[{title}]\nURL: {url}\n{text}")
                        # Track source with url and title for OpenWebUI display
                        if not any(s["url"] == url for s in all_sources):
                            all_sources.append({"url": url, "title": title})

                self.debug.search_results(len(search_results))
                # Show top sources in debug
                iter_sources = [{"url": r.get("url", ""), "title": r.get("title", "")} for r in search_results if r.get("url")]
                self.debug.sources_found(iter_sources)

                # ─── Agent Evaluation ─────────────────────────────────────────────
                await _status("Analyzing findings...")

                # Build context for agent
                if all_findings:
                    previous_findings = f"## Previous Findings:\n{chr(10).join(all_findings)}"
                else:
                    previous_findings = "## Previous Findings:\nNone yet - this is the first search."

                if iteration_content:
                    new_content = "\n\n---\n\n".join(iteration_content[:8])
                    new_content_section = f"## New Search Results (from this iteration):\n{new_content[:15000]}"
                else:
                    new_content_section = "## New Search Results:\nNo content retrieved this iteration."

                agent_prompt = AGENTIC_SEARCH_PROMPT.format(
                    current_date=current_date,
                    user_request=query,
                    current_iteration=iteration,
                    max_iterations=max_iterations,
                    source_count=len(all_sources),
                    previous_findings=previous_findings,
                    new_content_section=new_content_section
                )

                agent_payload = {
                    "model": self.valves.agent_model,
                    "messages": [{"role": "user", "content": agent_prompt}],
                    "stream": False,
                }

                agent_res = await generate_with_parsing_retry(
                    request=__request__,
                    form_data=agent_payload,
                    user=user_obj,
                    debug=self.debug,
                    expected_keys=["choices", "content", "message"]
                )

                # Extract agent response
                if "choices" in agent_res and agent_res["choices"]:
                    agent_response = agent_res["choices"][0]["message"]["content"]
                elif "content" in agent_res:
                    agent_response = agent_res["content"]
                else:
                    agent_response = str(agent_res)

                self.debug.data("Agent response", agent_response, truncate=400)

                # Extract status for UI
                for line in agent_response.split("\n"):
                    if "STATUS_SUMMARY:" in line.upper():
                        await _status(line.split(":", 1)[1].strip()[:60])
                        break

                # Extract findings
                extracted_info = self._extract_section(agent_response, "EXTRACTED_INFO:")
                if extracted_info and extracted_info.lower() not in ["no new content", "none", ""]:
                    all_findings.append(f"[Iteration {iteration}]\n{extracted_info}")
                    self.debug.flow(f"Added findings from iteration {iteration}")

                # Extract decision
                decision = "CONTINUE"
                for line in agent_response.split("\n"):
                    if "DECISION:" in line.upper():
                        if "STOP" in line.upper():
                            decision = "STOP"
                        break

                # Show agent's evaluation in debug
                evaluation = self._extract_section(agent_response, "EVALUATION:")
                self.debug.agent_evaluation(evaluation)
                
                self.debug.agent_decision(decision)

                if decision == "STOP":
                    self.debug.flow("Agent determined information is sufficient")
                    final_agent_response = agent_response
                    break

                # If continuing, try to parse new search config from agent response
                if iteration < max_iterations:
                    new_config = self._parse_search_config(agent_response)
                    if new_config.get("queries"):
                        search_config = new_config
                        self.debug.flow(f"Agent updated search config with {len(new_config['queries'])} queries")
                    else:
                        self.debug.warning("No new queries in agent response, stopping")
                        break

            # ─── Phase 3: Format Final Output ─────────────────────────────────────
            await _status("Compiling research results...")
            self.debug.flow(f"Final output: {len(all_findings)} findings, {len(all_sources)} sources")

            if not all_findings:
                self.debug.warning("No findings collected")
                return {
                    "content": "I was unable to find relevant information for your request. Please try rephrasing your question.",
                }

            # Extract summary from agent's final response
            if final_agent_response:
                self.debug.flow("Extracting summary from agent's STOP response")
                research_summary = self._extract_section(final_agent_response, "RESEARCH_SUMMARY:")
                key_points = self._extract_section(final_agent_response, "KEY_POINTS:")

                if research_summary:
                    final_content = f"RESEARCH_SUMMARY:\n{research_summary}"
                    if key_points:
                        final_content += f"\n\nKEY_POINTS:\n{key_points}"
                    final_content += f"\n\nSOURCES_CONSULTED: {len(all_sources)}"
                else:
                    self.debug.warning("Could not extract RESEARCH_SUMMARY, using raw findings")
                    final_content = f"RESEARCH_FINDINGS:\n" + "\n\n".join(all_findings)
                    final_content += f"\n\nSOURCES_CONSULTED: {len(all_sources)}"
            else:
                self.debug.flow("Max iterations reached, using accumulated findings")
                final_content = f"RESEARCH_FINDINGS:\n" + "\n\n".join(all_findings)
                final_content += f"\n\nSOURCES_CONSULTED: {len(all_sources)}"

            await _status("Search complete.", done=True)
            self.debug.synthesis(f"Agentic search complete. {len(all_sources)} sources, {iteration} iterations.")

            # Emit citation events for each source (this is how OpenWebUI displays sources)
            if show_sources and __event_emitter__ and all_sources:
                self.debug.flow(f"Emitting {len(all_sources)} citation events")
                for source in all_sources:
                    await __event_emitter__({
                        "type": "citation",
                        "data": {
                            "document": [f"Source: {source['title']}"],
                            "metadata": [{
                                "date_accessed": datetime.now().isoformat(),
                                "source": source["title"],
                                "url": source["url"]
                            }],
                            "source": {"name": source["title"], "url": source["url"]}
                        }
                    })

            if self.debug.enabled:
                self.debug.metrics_summary()

            return {
                "content": final_content,
            }

        except Exception as e:
            self.debug.error(f"Agentic search failed: {e}")
            if self.debug.enabled:
                self.debug.metrics_summary()
            try:
                await _status("", done=True)
            except Exception:
                pass
            return {
                "content": f"I encountered an error during the search: {e}",
            }


# Final tool definition for OpenWebUI
class Tools:
    """Main class that OpenWebUI will use"""

    def __init__(self):
        self.tools_instance = ToolsInternal()
        self.citation = False  # REQUIRED: Disable automatic citations so custom citation events work
        # Expose valves directly at the top level for OpenWebUI
        self.valves = self.tools_instance.valves

    class Valves(BaseModel):
        exa_api_key: str = Field(default="", description="Your Exa API key.")
        agent_model: str = Field(
            default="gpt-4o-mini",
            description="LLM model for the agentic search (extraction, evaluation, query generation).",
        )
        max_iterations: int = Field(
            default=3,
            description="Maximum number of search iterations before returning results.",
        )
        debug_enabled: bool = Field(
            default=False,
            description="Enable detailed debug logging for troubleshooting search operations.",
        )
        show_sources: bool = Field(
            default=False,
            description="If true, emit citation events so sources appear in the UI.",
        )

    async def agentic_search(
        self,
        query: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
        __messages__: Optional[List[Dict]] = None,
    ) -> dict:
        """Perform an intelligent agentic web search with full control over search parameters."""
        # Create debug instance with consistent formatting
        debug = Debug(enabled=self.valves.debug_enabled)
        debug.flow("agentic_search function called")
        debug.data("Query", query[:50] + "..." if len(query) > 50 else query)

        # Sync valve settings to internal instance
        self.tools_instance.valves = self.valves

        return await self.tools_instance.agentic_search(
            query, __event_emitter__, __request__, __user__, __messages__
        )
