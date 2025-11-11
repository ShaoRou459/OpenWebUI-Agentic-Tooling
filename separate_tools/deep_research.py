"""
Title: Deep Research Tool
Description: Multi-iteration comprehensive research with iterative query generation (COMPLETE mode)
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 1.0.0
Requirements: exa_py, open_webui
"""

import os
import json
import re
import asyncio
from typing import Any, Callable, Awaitable, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from open_webui.utils.chat import generate_chat_completion

try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    Exa = None
    EXA_AVAILABLE = False


# System prompts for the iterative research system
INTRODUCTORY_QUERY_PROMPT = """
You are an information-seeking specialist. Generate an introductory search query that helps understand the context and background of what the user is asking about.

CURRENT DATE: {current_date}

This query should be INFORMATIONAL, not trying to answer their question directly. Think of it as "What do I need to know about this topic first?"

Examples:
- User: "How do I optimize my React app performance?" → "React application performance optimization techniques"
- User: "What's the latest news about OpenAI?" → "OpenAI company recent developments {current_year}"

Output your introductory query on a line starting with "QUERY: "
"""

OBJECTIVE_SETTING_PROMPT = """
You are a research strategist. Based on the user's request and introductory information gathered, set clear research objectives.

CURRENT DATE: {current_date}

Analyze:
1. What exactly is the user asking for?
2. What are the key components of their request?
3. What direction should the research take?

Output a structured analysis with:
OBJECTIVES: [List 3-5 specific research objectives]
RESEARCH_DIRECTION: [Brief description of the overall research approach]
KEY_COMPONENTS: [List the main parts of the user's request that need to be addressed]
"""

ITERATION_REASONING_PROMPT = """
You are a research iteration planner. Based on your current knowledge and what you've found so far, reason about what to search for next.

CURRENT DATE: {current_date}

Current situation:
- Research objectives: {objectives}
- Previous findings summary: {previous_findings}
- Iteration: {current_iteration} of {max_iterations}

Your task:
1. Analyze what you've learned so far
2. Identify what's still missing
3. Reason about the best search approach for this iteration
4. Generate {query_count} diverse, specific search queries

Note: For time-sensitive topics, include {current_year} in your queries when relevant.

Output format:
ANALYSIS: [What you've learned and what's missing]
REASONING: [Why these specific searches will help]
QUERIES: ["query1", "query2", "query3", ...]
"""

ITERATION_CONCLUSION_PROMPT = """
You are a research analyst. Summarize what you found in this iteration and determine next steps.

CURRENT DATE: {current_date}
ITERATION: {current_iteration} of {max_iterations}

Provide:
FINDINGS_SUMMARY: [Key information discovered this iteration - be concise but comprehensive]
PROGRESS_ASSESSMENT: [How much closer are you to answering the user's question?]
NEXT_STEPS: [What should the next iteration focus on, or should research conclude?]
DECISION: [CONTINUE or FINISH]

Note: If this is iteration {max_iterations}, you must decide FINISH unless critical information is still missing.
"""

FINAL_SYNTHESIS_PROMPT = """
You are an information organizer. Your job is to structure the research findings so the chat model can effectively answer the user's question.

CURRENT DATE: {current_date}

Using the research chain and findings summaries, organize the information into a clear, comprehensive knowledge base that covers:
- Key facts and findings relevant to the user's question
- Important context and background information
- Relevant developments, especially recent ones when applicable
- Different perspectives or approaches discovered
- Any actionable insights or recommendations found

Structure this as organized, factual information that provides the chat model with everything needed to give a complete response to the user's original question. Focus on being comprehensive and well-organized rather than directly answering.

Include raw URLs or direct quotes from sources when needed.
"""


class Tools:
    """Deep Research Tool for OpenWebUI - comprehensive multi-iteration research"""

    class Valves(BaseModel):
        exa_api_key: str = Field(
            default="",
            description="Your Exa API key for web search."
        )
        agent_model: str = Field(
            default="gpt-4-turbo",
            description="The model for all agentic steps (reasoning, deciding, query generation)."
        )
        synthesizer_model: str = Field(
            default="gpt-4-turbo",
            description="Dedicated model for the final synthesis."
        )
        urls_per_query: int = Field(
            default=5,
            description="Number of URLs to fetch for each query."
        )
        urls_to_crawl: int = Field(
            default=3,
            description="Number of top URLs to crawl for each query."
        )
        queries_per_iteration: int = Field(
            default=3,
            description="Number of queries to generate per iteration."
        )
        max_iterations: int = Field(
            default=2,
            description="Maximum number of research iterations."
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

    async def deep_research(
        self,
        query: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
    ) -> str:
        """
        Conduct comprehensive, multi-iteration research on a topic.

        This tool performs iterative research with multiple search cycles,
        reasoning about what information is still needed, and synthesizing
        findings into a comprehensive knowledge base.

        Args:
            query: The research question or topic
            __event_emitter__: OpenWebUI event emitter for status updates
            __request__: Request object from OpenWebUI
            __user__: User object from OpenWebUI

        Returns:
            Comprehensive research findings formatted as a knowledge base

        Examples:
            await deep_research("What are the latest developments in quantum computing and their practical applications?")
        """
        # Check if Exa is available
        if not EXA_AVAILABLE:
            error_msg = "❌ Deep research unavailable: exa_py module not installed. Please install with: pip install exa_py"
            return error_msg

        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_year = datetime.now().year

            # Phase 1: Generate introductory query
            await _status("Gathering initial context...")

            intro_query = await self._generate_intro_query(query, current_date, current_year, __request__, __user__)

            # Search with introductory query
            intro_content = await self._search_and_get_content(intro_query, _status, __request__, __user__)

            if not intro_content:
                intro_content = "Unable to gather initial context. Proceeding with research based on query directly."

            # Phase 2: Set research objectives
            await _status("Setting research objectives...")

            objectives = await self._set_objectives(query, intro_content, current_date, __request__, __user__)

            # Phase 3: Iterative research
            research_chain = [
                f"INITIAL CONTEXT: {intro_content[:10000]}...",
                f"OBJECTIVES: {objectives}"
            ]
            previous_findings = "Initial context gathered from introductory search."

            for iteration in range(1, self.valves.max_iterations + 1):
                await _status(f"Research iteration {iteration}/{self.valves.max_iterations}...")

                # Generate queries for this iteration
                queries = await self._generate_iteration_queries(
                    objectives, previous_findings, iteration, current_date, current_year, __request__, __user__
                )

                # Execute searches
                iteration_findings = []
                for search_query in queries:
                    await _status(f"Searching: {search_query[:40]}...")
                    content = await self._search_and_get_content(search_query, _status, __request__, __user__)
                    if content:
                        iteration_findings.append(content)

                # Conclude iteration
                await _status(f"Analyzing iteration {iteration} findings...")

                iteration_content = "\n\n".join(iteration_findings) if iteration_findings else "No significant findings in this iteration."

                conclusion = await self._conclude_iteration(
                    query, objectives, previous_findings, iteration_content, iteration, current_date, __request__, __user__
                )

                # Extract findings summary and decision
                findings_summary = self._extract_field(conclusion, "FINDINGS_SUMMARY:")
                decision = self._extract_field(conclusion, "DECISION:")

                research_chain.append(f"ITERATION {iteration}: {findings_summary}")
                previous_findings = findings_summary

                if decision == "FINISH" or iteration == self.valves.max_iterations:
                    break

            # Phase 4: Final synthesis
            await _status("Synthesizing comprehensive answer...")

            research_summary = "\n\n".join(research_chain)
            final_answer = await self._synthesize_final_answer(query, research_summary, current_date, __request__, __user__)

            await _status("✓ Research complete", done=True)

            return final_answer

        except Exception as e:
            await _status("", done=True)
            return f"❌ Deep research failed: {str(e)}"

    async def _generate_intro_query(self, query: str, current_date: str, current_year: int, request, user) -> str:
        """Generate introductory search query."""
        payload = {
            "model": self.valves.agent_model,
            "messages": [
                {"role": "system", "content": INTRODUCTORY_QUERY_PROMPT.format(current_date=current_date, current_year=current_year)},
                {"role": "user", "content": f"User's request: {query}"},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        response_text = resp["choices"][0]["message"]["content"]

        # Extract query
        for line in response_text.split("\n"):
            if line.strip().startswith("QUERY:"):
                return line.split("QUERY:", 1)[1].strip()

        # Fallback
        return query

    async def _set_objectives(self, query: str, intro_content: str, current_date: str, request, user) -> str:
        """Set research objectives."""
        payload = {
            "model": self.valves.agent_model,
            "messages": [
                {"role": "system", "content": OBJECTIVE_SETTING_PROMPT.format(current_date=current_date)},
                {"role": "user", "content": f"User's request: {query}\n\nIntroductory information:\n{intro_content}"},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        return resp["choices"][0]["message"]["content"]

    async def _generate_iteration_queries(self, objectives: str, previous_findings: str, iteration: int, current_date: str, current_year: int, request, user) -> List[str]:
        """Generate search queries for an iteration."""
        prompt = ITERATION_REASONING_PROMPT.format(
            current_date=current_date,
            current_year=current_year,
            objectives=objectives[:6000],
            previous_findings=previous_findings[:16000],
            current_iteration=iteration,
            max_iterations=self.valves.max_iterations,
            query_count=self.valves.queries_per_iteration
        )

        payload = {
            "model": self.valves.agent_model,
            "messages": [
                {"role": "system", "content": "You are a research iteration planner."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        response_text = resp["choices"][0]["message"]["content"]

        # Extract queries - try multiple methods
        queries = []

        # Method 1: Look for JSON array
        for line in response_text.split("\n"):
            if "QUERIES:" in line.upper() and "[" in line and "]" in line:
                try:
                    query_part = line.split("QUERIES:")[-1].strip()
                    queries = json.loads(query_part)
                    break
                except json.JSONDecodeError:
                    pass

        # Method 2: Extract quoted strings
        if not queries:
            quoted_queries = re.findall(r'"([^"]*)"', response_text)
            if quoted_queries:
                queries = [q for q in quoted_queries if len(q) > 5]

        # Method 3: Look for list-style queries
        if not queries:
            lines = response_text.split("\n")
            for line in lines:
                if line.strip().startswith(("-", "*", "1.", "2.", "3.")):
                    query = line.strip().lstrip("-*123456789. ").strip()
                    if len(query) > 10:
                        queries.append(query)

        # Fallback
        if not queries:
            queries = [f"detailed research iteration {iteration}"]

        return queries[:self.valves.queries_per_iteration]

    async def _conclude_iteration(self, query: str, objectives: str, previous_findings: str, iteration_content: str, iteration: int, current_date: str, request, user) -> str:
        """Conclude an iteration and decide next steps."""
        conclusion_prompt = f"""
        Research findings from iteration {iteration}:
        {iteration_content}

        User's original question: {query}
        Research objectives: {objectives}
        Previous findings summary: {previous_findings}

        Analyze these findings and determine next steps.
        """

        payload = {
            "model": self.valves.agent_model,
            "messages": [
                {"role": "system", "content": ITERATION_CONCLUSION_PROMPT.format(
                    current_date=current_date,
                    current_iteration=iteration,
                    max_iterations=self.valves.max_iterations
                )},
                {"role": "user", "content": conclusion_prompt},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        return resp["choices"][0]["message"]["content"]

    async def _synthesize_final_answer(self, query: str, research_summary: str, current_date: str, request, user) -> str:
        """Synthesize final comprehensive answer."""
        payload = {
            "model": self.valves.synthesizer_model,
            "messages": [
                {"role": "system", "content": FINAL_SYNTHESIS_PROMPT.format(current_date=current_date)},
                {"role": "user", "content": f"User's original question: {query}\n\nResearch progression and findings:\n{research_summary}"},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        return resp["choices"][0]["message"]["content"]

    async def _search_and_get_content(self, query: str, status_func, request, user) -> str:
        """Search and retrieve content for a query."""
        try:
            exa = self._exa_client()

            # Search
            search_results = await asyncio.to_thread(
                exa.search,
                query,
                num_results=self.valves.urls_per_query
            )

            if not search_results.results:
                return ""

            # Crawl
            ids_to_crawl = [res.id for res in search_results.results[:self.valves.urls_to_crawl]]
            crawled_results = await asyncio.to_thread(
                exa.get_contents,
                ids_to_crawl
            )

            if not crawled_results.results:
                return ""

            # Extract content
            texts = []
            for res in crawled_results.results:
                if res.text and res.text.strip():
                    title = getattr(res, "title", "Unknown Source")
                    text_summary = ' '.join(res.text.split()[:3000])
                    if text_summary:
                        texts.append(f"From {title}: {text_summary}")

            return "\n\n".join(texts)

        except Exception:
            return ""

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field from formatted text."""
        for line in text.split("\n"):
            if field_name.upper() in line.upper():
                return line.split(":", 1)[1].strip() if ":" in line else ""
        return ""
