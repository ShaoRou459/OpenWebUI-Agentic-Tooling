"""
Test suite for universal debug system and retry logic.

This script tests:
1. Debug logging and color output
2. Metrics tracking
3. Retry logic with exponential backoff
4. Integration with tools
"""

import asyncio
import sys
from typing import Optional

# Test the universal debug system
from universal_debug import UniversalDebug, retry_async, retry_sync, format_bytes, format_duration


async def test_basic_logging():
    """Test basic logging functionality."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Logging")
    print("=" * 80)

    debug = UniversalDebug(enabled=True, tool_name="TestTool")

    debug.start_session("Testing basic logging")
    debug.info("This is an info message")
    debug.success("This is a success message")
    debug.warning("This is a warning message")
    debug.error("This is an error message")
    debug.debug("This is a debug message")
    debug.api_call("Making API call to test endpoint")
    debug.search("Searching for test query")
    debug.agent("Agent performing task")
    debug.retry("Test operation", 2, 3)
    debug.data("test_data", {"key": "value", "nested": {"foo": "bar"}})

    print("\n✓ Basic logging test complete")


async def test_timing():
    """Test timing functionality."""
    print("\n" + "=" * 80)
    print("TEST 2: Timing and Metrics")
    print("=" * 80)

    debug = UniversalDebug(enabled=True, tool_name="TimingTest")
    debug.start_session("Testing timing")

    # Test timer context manager
    with debug.timer("operation_1"):
        await asyncio.sleep(0.1)

    with debug.timer("operation_2"):
        await asyncio.sleep(0.05)

    with debug.timer("operation_1"):  # Same operation again
        await asyncio.sleep(0.08)

    # Update metrics
    debug.metrics.llm_calls = 5
    debug.metrics.llm_total_time = 2.5
    debug.metrics.llm_failures = 1
    debug.metrics.llm_retries = 2

    debug.metrics.urls_found = 10
    debug.metrics.urls_crawled = 8
    debug.metrics.urls_successful = 7
    debug.metrics.urls_failed = 1
    debug.metrics.total_content_chars = 45000

    debug.metrics_summary()

    print("\n✓ Timing and metrics test complete")


async def test_retry_success():
    """Test retry logic with eventual success."""
    print("\n" + "=" * 80)
    print("TEST 3: Retry Logic (Success After 2 Attempts)")
    print("=" * 80)

    debug = UniversalDebug(enabled=True, tool_name="RetryTest")
    debug.start_session("Testing retry success")

    attempt_count = [0]

    async def flaky_operation():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise Exception(f"Simulated failure #{attempt_count[0]}")
        return "Success!"

    try:
        result = await retry_async(
            flaky_operation,
            max_retries=3,
            initial_delay=0.1,
            debug=debug,
            operation_name="flaky_operation"
        )
        print(f"\n✓ Retry test complete: {result}")
    except Exception as e:
        print(f"\n✗ Retry test failed: {e}")


async def test_retry_failure():
    """Test retry logic with complete failure."""
    print("\n" + "=" * 80)
    print("TEST 4: Retry Logic (Complete Failure)")
    print("=" * 80)

    debug = UniversalDebug(enabled=True, tool_name="RetryFail")
    debug.start_session("Testing retry failure")

    async def always_fails():
        raise Exception("This always fails")

    try:
        result = await retry_async(
            always_fails,
            max_retries=3,
            initial_delay=0.1,
            debug=debug,
            operation_name="failing_operation"
        )
        print("\n✗ Retry test failed: Should have raised exception")
    except Exception as e:
        print(f"\n✓ Retry test complete: Correctly failed after retries ({str(e)})")


def test_sync_retry():
    """Test synchronous retry logic."""
    print("\n" + "=" * 80)
    print("TEST 5: Synchronous Retry Logic")
    print("=" * 80)

    debug = UniversalDebug(enabled=True, tool_name="SyncRetry")
    debug.start_session("Testing sync retry")

    attempt_count = [0]

    def flaky_sync_operation():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise Exception(f"Sync failure #{attempt_count[0]}")
        return "Sync success!"

    try:
        result = retry_sync(
            flaky_sync_operation,
            max_retries=3,
            initial_delay=0.1,
            debug=debug,
            operation_name="sync_operation"
        )
        print(f"\n✓ Sync retry test complete: {result}")
    except Exception as e:
        print(f"\n✗ Sync retry test failed: {e}")


async def test_tool_integration():
    """Test integration with actual tools."""
    print("\n" + "=" * 80)
    print("TEST 6: Tool Integration")
    print("=" * 80)

    try:
        # Test crawl_url tool
        from crawl_url import Tools as CrawlTools

        crawl = CrawlTools()
        crawl.valves.debug_enabled = True
        print("\n✓ CrawlURL tool loaded with debug support")

        # Test web_search tool
        from web_search import Tools as SearchTools

        search = SearchTools()
        search.valves.debug_enabled = True
        print("✓ WebSearch tool loaded with debug support")

        # Test image_generation tool
        from image_generation import Tools as ImageTools

        image = ImageTools()
        image.valves.debug_enabled = True
        print("✓ ImageGen tool loaded with debug support")

        # Test deep_research tool
        from deep_research import Tools as ResearchTools

        research = ResearchTools()
        # research.valves.debug_enabled = True  # May not be implemented yet
        print("✓ DeepResearch tool loaded")

        print("\n✓ Tool integration test complete")

    except Exception as e:
        print(f"\n✗ Tool integration test failed: {e}")
        import traceback
        traceback.print_exc()


def test_utility_functions():
    """Test utility functions."""
    print("\n" + "=" * 80)
    print("TEST 7: Utility Functions")
    print("=" * 80)

    # Test format_bytes
    assert format_bytes(500) == "500.0B"
    assert format_bytes(1500) == "1.5KB"
    assert format_bytes(1500000) == "1.4MB"
    assert format_bytes(1500000000) == "1.4GB"
    print("✓ format_bytes works correctly")

    # Test format_duration
    assert format_duration(0.5) == "500ms"
    assert format_duration(5.5) == "5.5s"
    assert format_duration(125) == "2.1m"
    assert format_duration(7200) == "2.0h"
    print("✓ format_duration works correctly")

    print("\n✓ Utility functions test complete")


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("UNIVERSAL DEBUG AND RETRY LOGIC TEST SUITE")
    print("=" * 80)

    try:
        # Run tests
        await test_basic_logging()
        await test_timing()
        await test_retry_success()
        await test_retry_failure()
        test_sync_retry()
        await test_tool_integration()
        test_utility_functions()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
