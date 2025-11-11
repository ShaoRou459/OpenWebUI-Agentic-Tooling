"""
Comprehensive tests for all separate OpenWebUI tools.

These tests verify:
1. Tool initialization
2. Basic functionality
3. Error handling
4. Response formatting

To run these tests:
    python -m pytest test_tools.py -v

or

    python test_tools.py
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock


class TestCrawlURLTool(unittest.TestCase):
    """Test suite for the URL Crawler tool"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock the exa_py import
        self.mock_exa = MagicMock()
        sys.modules['exa_py'] = self.mock_exa

        # Import the tool
        from crawl_url import Tools
        self.tool = Tools()
        self.tool.valves.exa_api_key = "test_key"

    def test_tool_initialization(self):
        """Test that the tool initializes correctly"""
        self.assertIsNotNone(self.tool)
        self.assertIsNotNone(self.tool.valves)
        self.assertEqual(self.tool.valves.exa_api_key, "test_key")

    def test_invalid_url(self):
        """Test handling of invalid URLs"""
        async def run_test():
            result = await self.tool.crawl_url("not a url")
            self.assertIn("Invalid URL", result)

        asyncio.run(run_test())

    def test_empty_url(self):
        """Test handling of empty URLs"""
        async def run_test():
            result = await self.tool.crawl_url("")
            self.assertIn("Invalid URL", result)

        asyncio.run(run_test())

    def test_crawl_success_format(self):
        """Test that successful crawl returns properly formatted content"""
        # Mock the Exa client
        mock_result = Mock()
        mock_result.text = "This is test content from the web page."
        mock_result.url = "https://example.com"

        mock_contents = Mock()
        mock_contents.results = [mock_result]

        mock_exa_instance = Mock()
        mock_exa_instance.get_contents = Mock(return_value=mock_contents)

        self.tool._exa = mock_exa_instance

        async def run_test():
            result = await self.tool.crawl_url("https://example.com")
            self.assertIn("# Content from", result)
            self.assertIn("example.com", result)
            self.assertIn("test content", result)

        asyncio.run(run_test())


class TestWebSearchTool(unittest.TestCase):
    """Test suite for the Web Search tool"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock the exa_py import
        self.mock_exa = MagicMock()
        sys.modules['exa_py'] = self.mock_exa

        # Import the tool
        from web_search import Tools
        self.tool = Tools()
        self.tool.valves.exa_api_key = "test_key"

    def test_tool_initialization(self):
        """Test that the tool initializes correctly"""
        self.assertIsNotNone(self.tool)
        self.assertIsNotNone(self.tool.valves)
        self.assertEqual(self.tool.valves.urls_to_search, 5)
        self.assertEqual(self.tool.valves.urls_to_crawl, 3)

    def test_empty_query(self):
        """Test handling of empty queries"""
        async def run_test():
            result = await self.tool.web_search("")
            self.assertIn("Empty search query", result)

        asyncio.run(run_test())

    def test_response_format(self):
        """Test that the response is properly formatted for AI consumption"""
        # Mock search results
        mock_search_result = Mock()
        mock_search_result.id = "test_id_1"
        mock_search_result.url = "https://example.com/article1"

        mock_search_response = Mock()
        mock_search_response.results = [mock_search_result]

        # Mock crawl results
        mock_crawl_result = Mock()
        mock_crawl_result.url = "https://example.com/article1"
        mock_crawl_result.title = "Test Article"
        mock_crawl_result.text = "This is test content from the article."

        mock_crawl_response = Mock()
        mock_crawl_response.results = [mock_crawl_result]

        # Set up mock Exa client
        mock_exa_instance = Mock()
        mock_exa_instance.search = Mock(return_value=mock_search_response)
        mock_exa_instance.get_contents = Mock(return_value=mock_crawl_response)

        self.tool._exa = mock_exa_instance

        async def run_test():
            result = await self.tool.web_search("test query")

            # Verify structured format
            self.assertIn("# Web Search Results", result)
            self.assertIn("**Query:**", result)
            self.assertIn("**Sources Retrieved:**", result)
            self.assertIn("## Source 1:", result)
            self.assertIn("**URL:**", result)
            self.assertIn("**Domain:**", result)
            self.assertIn("**Content:**", result)
            self.assertIn("**Instructions for AI Model:**", result)

        asyncio.run(run_test())


class TestDeepResearchTool(unittest.TestCase):
    """Test suite for the Deep Research tool"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock the exa_py import
        self.mock_exa = MagicMock()
        sys.modules['exa_py'] = self.mock_exa

        # Mock the open_webui imports
        self.mock_chat = MagicMock()
        sys.modules['open_webui'] = MagicMock()
        sys.modules['open_webui.utils'] = MagicMock()
        sys.modules['open_webui.utils.chat'] = self.mock_chat

        # Import the tool
        from deep_research import Tools
        self.tool = Tools()
        self.tool.valves.exa_api_key = "test_key"

    def test_tool_initialization(self):
        """Test that the tool initializes correctly"""
        self.assertIsNotNone(self.tool)
        self.assertIsNotNone(self.tool.valves)
        self.assertEqual(self.tool.valves.max_iterations, 2)
        self.assertEqual(self.tool.valves.queries_per_iteration, 3)

    def test_valve_configuration(self):
        """Test that valve settings are configurable"""
        self.tool.valves.max_iterations = 5
        self.tool.valves.queries_per_iteration = 4

        self.assertEqual(self.tool.valves.max_iterations, 5)
        self.assertEqual(self.tool.valves.queries_per_iteration, 4)


class TestImageGenerationTool(unittest.TestCase):
    """Test suite for the Image Generation tool"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock the open_webui imports
        self.mock_chat = MagicMock()
        sys.modules['open_webui'] = MagicMock()
        sys.modules['open_webui.utils'] = MagicMock()
        sys.modules['open_webui.utils.chat'] = self.mock_chat

        # Import the tool
        from image_generation import Tools
        self.tool = Tools()

    def test_tool_initialization(self):
        """Test that the tool initializes correctly"""
        self.assertIsNotNone(self.tool)
        self.assertIsNotNone(self.tool.valves)
        self.assertEqual(self.tool.valves.image_gen_model, "gpt-4o-image")

    def test_empty_prompt(self):
        """Test handling of empty prompts"""
        async def run_test():
            result = await self.tool.generate_image("")
            self.assertIn("Empty image prompt", result)

        asyncio.run(run_test())

    def test_description_auto_generation(self):
        """Test that description is auto-generated from prompt if not provided"""
        # Mock the generate_chat_completion function
        mock_response = {
            "choices": [{
                "message": {
                    "content": "https://example.com/generated_image.png"
                }
            }]
        }

        async def mock_generate(*args, **kwargs):
            return mock_response

        self.mock_chat.generate_chat_completion = mock_generate

        async def run_test():
            # Re-import to get mocked version
            from image_generation import Tools
            tool = Tools()

            with patch('image_generation.generate_chat_completion', new=mock_generate):
                result = await tool.generate_image("A beautiful sunset over mountains")

                # Check that markdown format is correct
                self.assertIn("![", result)
                self.assertIn("](", result)
                self.assertIn("https://", result)

        asyncio.run(run_test())


class IntegrationTests(unittest.TestCase):
    """Integration tests to verify tools work together"""

    def test_all_tools_importable(self):
        """Test that all tools can be imported without errors"""
        try:
            # Mock dependencies
            sys.modules['exa_py'] = MagicMock()
            sys.modules['open_webui'] = MagicMock()
            sys.modules['open_webui.utils'] = MagicMock()
            sys.modules['open_webui.utils.chat'] = MagicMock()

            from crawl_url import Tools as CrawlTools
            from web_search import Tools as SearchTools
            from deep_research import Tools as ResearchTools
            from image_generation import Tools as ImageTools

            # Verify each tool can be instantiated
            crawl = CrawlTools()
            search = SearchTools()
            research = ResearchTools()
            image = ImageTools()

            self.assertIsNotNone(crawl)
            self.assertIsNotNone(search)
            self.assertIsNotNone(research)
            self.assertIsNotNone(image)

        except Exception as e:
            self.fail(f"Failed to import tools: {e}")

    def test_all_tools_have_valves(self):
        """Test that all tools have properly configured Valves"""
        # Mock dependencies
        sys.modules['exa_py'] = MagicMock()
        sys.modules['open_webui'] = MagicMock()
        sys.modules['open_webui.utils'] = MagicMock()
        sys.modules['open_webui.utils.chat'] = MagicMock()

        from crawl_url import Tools as CrawlTools
        from web_search import Tools as SearchTools
        from deep_research import Tools as ResearchTools
        from image_generation import Tools as ImageTools

        tools = [CrawlTools(), SearchTools(), ResearchTools(), ImageTools()]

        for tool in tools:
            self.assertTrue(hasattr(tool, 'valves'))
            self.assertIsNotNone(tool.valves)


def run_basic_tests():
    """Run basic sanity checks without pytest"""
    print("=" * 80)
    print("Running Basic Tool Tests")
    print("=" * 80)

    # Mock all dependencies
    sys.modules['exa_py'] = MagicMock()
    sys.modules['open_webui'] = MagicMock()
    sys.modules['open_webui.utils'] = MagicMock()
    sys.modules['open_webui.utils.chat'] = MagicMock()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Import all tools
    print("\n[TEST 1] Importing all tools...")
    try:
        from crawl_url import Tools as CrawlTools
        from web_search import Tools as SearchTools
        from deep_research import Tools as ResearchTools
        from image_generation import Tools as ImageTools
        print("✓ All tools imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Failed to import tools: {e}")
        tests_failed += 1
        return

    # Test 2: Instantiate all tools
    print("\n[TEST 2] Instantiating all tools...")
    try:
        crawl = CrawlTools()
        search = SearchTools()
        research = ResearchTools()
        image = ImageTools()
        print("✓ All tools instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Failed to instantiate tools: {e}")
        tests_failed += 1
        return

    # Test 3: Verify Valves
    print("\n[TEST 3] Verifying Valves configuration...")
    try:
        assert hasattr(crawl, 'valves'), "CrawlTools missing valves"
        assert hasattr(search, 'valves'), "SearchTools missing valves"
        assert hasattr(research, 'valves'), "ResearchTools missing valves"
        assert hasattr(image, 'valves'), "ImageTools missing valves"
        print("✓ All tools have Valves")
        tests_passed += 1
    except AssertionError as e:
        print(f"✗ Valves verification failed: {e}")
        tests_failed += 1

    # Test 4: Verify tool methods exist
    print("\n[TEST 4] Verifying tool methods...")
    try:
        assert hasattr(crawl, 'crawl_url'), "CrawlTools missing crawl_url method"
        assert hasattr(search, 'web_search'), "SearchTools missing web_search method"
        assert hasattr(research, 'deep_research'), "ResearchTools missing deep_research method"
        assert hasattr(image, 'generate_image'), "ImageTools missing generate_image method"
        print("✓ All tools have required methods")
        tests_passed += 1
    except AssertionError as e:
        print(f"✗ Method verification failed: {e}")
        tests_failed += 1

    # Test 5: Verify Exa-based tools have API key valve
    print("\n[TEST 5] Verifying API key configuration...")
    try:
        assert hasattr(crawl.valves, 'exa_api_key'), "CrawlTools missing exa_api_key valve"
        assert hasattr(search.valves, 'exa_api_key'), "SearchTools missing exa_api_key valve"
        assert hasattr(research.valves, 'exa_api_key'), "ResearchTools missing exa_api_key valve"
        print("✓ All Exa-based tools have API key valve")
        tests_passed += 1
    except AssertionError as e:
        print(f"✗ API key verification failed: {e}")
        tests_failed += 1

    # Test 6: Verify configuration parameters
    print("\n[TEST 6] Verifying configuration parameters...")
    try:
        assert search.valves.urls_to_search == 5, "SearchTools urls_to_search incorrect"
        assert search.valves.urls_to_crawl == 3, "SearchTools urls_to_crawl incorrect"
        assert research.valves.max_iterations == 2, "ResearchTools max_iterations incorrect"
        assert image.valves.image_gen_model == "gpt-4o-image", "ImageTools model incorrect"
        print("✓ All configuration parameters are correct")
        tests_passed += 1
    except AssertionError as e:
        print(f"✗ Configuration verification failed: {e}")
        tests_failed += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"Test Summary: {tests_passed} passed, {tests_failed} failed")
    print("=" * 80)

    return tests_failed == 0


if __name__ == "__main__":
    # Run basic tests that don't require pytest
    success = run_basic_tests()

    print("\n" + "=" * 80)
    if success:
        print("✓ All basic tests passed!")
        print("\nTo run full test suite with pytest:")
        print("  pip install pytest")
        print("  pytest test_tools.py -v")
    else:
        print("✗ Some tests failed. Please review the output above.")
    print("=" * 80)

    sys.exit(0 if success else 1)
