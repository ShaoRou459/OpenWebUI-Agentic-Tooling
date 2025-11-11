"""
Universal Debug and Logging System for OpenWebUI Tools

This module provides a comprehensive, color-coded debugging and logging
system with retry logic that can be used across all OpenWebUI tools.

Features:
- Color-coded console output
- Structured logging with timestamps
- Metrics tracking (timing, API calls, errors)
- Retry logic with exponential backoff
- Context managers for timing operations
"""

import sys
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import contextmanager


# ============================================================================
# ANSI Color Codes
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"

    # Basic colors
    BLACK = "\x1b[30m"
    RED = "\x1b[91m"
    GREEN = "\x1b[92m"
    YELLOW = "\x1b[93m"
    BLUE = "\x1b[94m"
    MAGENTA = "\x1b[95m"
    CYAN = "\x1b[96m"
    WHITE = "\x1b[97m"

    # Extended colors
    ORANGE = "\x1b[38;5;208m"
    PURPLE = "\x1b[38;5;129m"
    PINK = "\x1b[38;5;213m"
    LIME = "\x1b[38;5;154m"


# ============================================================================
# Metrics Tracking
# ============================================================================

@dataclass
class DebugMetrics:
    """Collects and tracks metrics throughout execution."""

    # Timing metrics
    start_time: float = field(default_factory=time.perf_counter)
    operation_times: Dict[str, float] = field(default_factory=dict)
    total_operations: int = 0

    # API/LLM metrics
    llm_calls: int = 0
    llm_total_time: float = 0.0
    llm_failures: int = 0
    llm_retries: int = 0

    # Search/API metrics
    api_calls: int = 0
    api_failures: int = 0
    api_retries: int = 0

    # Content metrics
    total_content_chars: int = 0
    urls_found: int = 0
    urls_crawled: int = 0
    urls_successful: int = 0
    urls_failed: int = 0

    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_operation_time(self, operation: str, duration: float) -> None:
        """Add timing data for an operation."""
        self.operation_times[operation] = self.operation_times.get(operation, 0) + duration
        self.total_operations += 1

    def add_error(self, error: str) -> None:
        """Add an error to tracking."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.errors.append(f"[{timestamp}] {error}")

    def add_warning(self, warning: str) -> None:
        """Add a warning to tracking."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.warnings.append(f"[{timestamp}] {warning}")

    def get_total_time(self) -> float:
        """Get total elapsed time since start."""
        return time.perf_counter() - self.start_time


# ============================================================================
# Universal Debug Logger
# ============================================================================

class UniversalDebug:
    """
    Universal debug logging system with color-coded output and metrics tracking.

    Usage:
        debug = UniversalDebug(enabled=True, tool_name="WebSearch")
        debug.info("Starting search...")
        debug.success("Search completed!")
        debug.error("Something went wrong")
    """

    def __init__(self, enabled: bool = False, tool_name: str = "Tool"):
        self.enabled = enabled
        self.tool_name = tool_name
        self.metrics = DebugMetrics()
        self._session_id = str(int(time.time()))[-6:]

    def _get_timestamp(self) -> str:
        """Get formatted timestamp with milliseconds."""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _format_message(
        self,
        category: str,
        message: str,
        color: str = "CYAN",
        include_timestamp: bool = True
    ) -> str:
        """Format a debug message with consistent styling."""
        if not self.enabled:
            return ""

        timestamp = f"{Colors.DIM}[{self._get_timestamp()}]{Colors.RESET} " if include_timestamp else ""
        prefix = f"{Colors.MAGENTA}{Colors.BOLD}[{self.tool_name}:{self._session_id}]{Colors.RESET}"
        cat_colored = f"{getattr(Colors, color)}{Colors.BOLD}{category:<12}{Colors.RESET}"
        msg_colored = f"{getattr(Colors, color)}{message}{Colors.RESET}"

        return f"{timestamp}{prefix} {cat_colored}: {msg_colored}"

    def _log(self, category: str, message: str, color: str = "CYAN") -> None:
        """Internal logging method."""
        if self.enabled:
            formatted = self._format_message(category, message, color)
            if formatted:
                print(formatted, file=sys.stderr)

    # ========================================================================
    # Logging Methods
    # ========================================================================

    def info(self, message: str) -> None:
        """Log informational message."""
        self._log("INFO", message, "CYAN")

    def success(self, message: str) -> None:
        """Log success message."""
        self._log("SUCCESS", message, "GREEN")

    def warning(self, message: str) -> None:
        """Log warning message."""
        self._log("WARNING", message, "YELLOW")
        self.metrics.add_warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self._log("ERROR", message, "RED")
        self.metrics.add_error(message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self._log("DEBUG", message, "DIM")

    def api_call(self, message: str) -> None:
        """Log API call."""
        self._log("API", message, "BLUE")
        self.metrics.api_calls += 1

    def search(self, message: str) -> None:
        """Log search operation."""
        self._log("SEARCH", message, "LIME")

    def agent(self, message: str) -> None:
        """Log agent operation."""
        self._log("AGENT", message, "PURPLE")

    def retry(self, message: str, attempt: int, max_attempts: int) -> None:
        """Log retry attempt."""
        self._log("RETRY", f"Attempt {attempt}/{max_attempts}: {message}", "ORANGE")

    def data(self, label: str, data: Any, truncate: int = 80) -> None:
        """Log data with optional truncation."""
        if not self.enabled:
            return

        data_str = str(data)
        if len(data_str) > truncate:
            data_str = f"{data_str[:truncate]}..."

        self._log("DATA", f"{label} → {data_str}", "DIM")

    @contextmanager
    def timer(self, operation_name: str):
        """Context manager for timing operations."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.metrics.add_operation_time(operation_name, duration)
            if self.enabled:
                self._log("TIMING", f"{operation_name} completed in {duration:.3f}s", "ORANGE")

    def start_session(self, description: str = "") -> None:
        """Start a new debug session."""
        self.metrics = DebugMetrics()
        session_msg = f"Debug session started" + (f": {description}" if description else "")
        self._log("SESSION", session_msg, "PURPLE")
        self._log("SESSION", f"Session ID: {self._session_id}", "DIM")

    # ========================================================================
    # Metrics Summary
    # ========================================================================

    def metrics_summary(self) -> None:
        """Display comprehensive metrics summary."""
        if not self.enabled:
            return

        total_time = self.metrics.get_total_time()

        lines = [
            "",
            "═" * 80,
            f"📊 METRICS SUMMARY - {self.tool_name} (Session: {self._session_id})",
            "═" * 80,
            "",
            "⏱️  TIMING:",
            f"   Total Time: {total_time:.3f}s",
            f"   Operations: {self.metrics.total_operations}",
        ]

        if self.metrics.operation_times:
            lines.append("   Breakdown:")
            for op, duration in sorted(self.metrics.operation_times.items(), key=lambda x: x[1], reverse=True):
                pct = (duration / total_time) * 100 if total_time > 0 else 0
                lines.append(f"     • {op}: {duration:.3f}s ({pct:.1f}%)")

        if self.metrics.llm_calls > 0:
            lines.extend([
                "",
                "🤖 LLM METRICS:",
                f"   Calls: {self.metrics.llm_calls}",
                f"   Total Time: {self.metrics.llm_total_time:.3f}s",
                f"   Failures: {self.metrics.llm_failures}",
                f"   Retries: {self.metrics.llm_retries}",
                f"   Avg Time: {(self.metrics.llm_total_time / self.metrics.llm_calls):.3f}s" if self.metrics.llm_calls > 0 else "   Avg Time: N/A",
            ])

        if self.metrics.api_calls > 0:
            lines.extend([
                "",
                "🔌 API METRICS:",
                f"   Calls: {self.metrics.api_calls}",
                f"   Failures: {self.metrics.api_failures}",
                f"   Retries: {self.metrics.api_retries}",
            ])

        if self.metrics.urls_found > 0:
            lines.extend([
                "",
                "🔍 SEARCH METRICS:",
                f"   URLs Found: {self.metrics.urls_found}",
                f"   URLs Crawled: {self.metrics.urls_crawled}",
                f"   URLs Successful: {self.metrics.urls_successful}",
                f"   URLs Failed: {self.metrics.urls_failed}",
                f"   Success Rate: {(self.metrics.urls_successful / self.metrics.urls_crawled * 100):.1f}%" if self.metrics.urls_crawled > 0 else "   Success Rate: N/A",
            ])

        if self.metrics.total_content_chars > 0:
            lines.extend([
                "",
                "📄 CONTENT:",
                f"   Total Characters: {self.metrics.total_content_chars:,}",
            ])

        if self.metrics.errors or self.metrics.warnings:
            lines.extend([
                "",
                "⚠️  ISSUES:",
                f"   Errors: {len(self.metrics.errors)}",
                f"   Warnings: {len(self.metrics.warnings)}",
            ])

            if self.metrics.errors:
                lines.append("   Recent Errors:")
                for error in self.metrics.errors[-3:]:
                    lines.append(f"     • {error}")

            if self.metrics.warnings:
                lines.append("   Recent Warnings:")
                for warning in self.metrics.warnings[-3:]:
                    lines.append(f"     • {warning}")

        lines.extend([
            "",
            "═" * 80,
            ""
        ])

        report = "\n".join(lines)
        formatted = self._format_message("METRICS", report, "PURPLE", include_timestamp=False)
        if formatted:
            print(formatted, file=sys.stderr)


# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================

async def retry_async(
    func: Callable[..., Awaitable[Any]],
    *args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    debug: Optional[UniversalDebug] = None,
    operation_name: str = "operation",
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        debug: Optional debug logger
        operation_name: Name of operation for logging
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            if debug and attempt > 0:
                debug.retry(operation_name, attempt + 1, max_retries)

            result = await func(*args, **kwargs)

            if debug and attempt > 0:
                debug.success(f"{operation_name} succeeded after {attempt + 1} attempts")

            return result

        except Exception as e:
            last_exception = e

            if debug:
                debug.error(f"{operation_name} failed (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}")

            # Don't wait on last attempt
            if attempt < max_retries - 1:
                # Calculate delay with exponential backoff
                delay = min(initial_delay * (exponential_base ** attempt), max_delay)

                if debug:
                    debug.info(f"Waiting {delay:.1f}s before retry...")

                await asyncio.sleep(delay)

    if debug:
        debug.error(f"{operation_name} failed after {max_retries} retries")

    raise last_exception


def retry_sync(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    debug: Optional[UniversalDebug] = None,
    operation_name: str = "operation",
    **kwargs
) -> Any:
    """
    Retry a sync function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        debug: Optional debug logger
        operation_name: Name of operation for logging
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            if debug and attempt > 0:
                debug.retry(operation_name, attempt + 1, max_retries)

            result = func(*args, **kwargs)

            if debug and attempt > 0:
                debug.success(f"{operation_name} succeeded after {attempt + 1} attempts")

            return result

        except Exception as e:
            last_exception = e

            if debug:
                debug.error(f"{operation_name} failed (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}")

            # Don't wait on last attempt
            if attempt < max_retries - 1:
                # Calculate delay with exponential backoff
                delay = min(initial_delay * (exponential_base ** attempt), max_delay)

                if debug:
                    debug.info(f"Waiting {delay:.1f}s before retry...")

                time.sleep(delay)

    if debug:
        debug.error(f"{operation_name} failed after {max_retries} retries")

    raise last_exception


# ============================================================================
# Utility Functions
# ============================================================================

def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f}TB"


def format_duration(seconds: float) -> str:
    """Format duration into human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
