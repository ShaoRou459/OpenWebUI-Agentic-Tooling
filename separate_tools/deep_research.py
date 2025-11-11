"""
Title: Deep Research Tool (Multi-Agent)
Description: Parallel multi-agent research system with independent sub-agents
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 2.0.0
Requirements: exa_py, open_webui
"""

import os
import json
import re
import asyncio
from typing import Any, Callable, Awaitable, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from dataclasses import dataclass

from open_webui.utils.chat import generate_chat_completion

try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    Exa = None
    EXA_AVAILABLE = False


# ============================================================================
# System Prompts for Multi-Agent Research
# ============================================================================

GOAL_DEFINITION_PROMPT = """
You are a research strategist. Analyze the user's question and define a clear, comprehensive research goal.

CURRENT DATE: {current_date}

Your task:
1. Understand what the user is truly asking
2. Define the overarching research goal
3. Clarify the scope and depth needed

User's Question: {user_query}

Output format:
GOAL: [A clear, comprehensive statement of what we need to research]
SCOPE: [What should be included and what should be excluded]
EXPECTED_DEPTH: [How deep should the research go - surface-level, moderate, or comprehensive]
"""

OBJECTIVE_IDENTIFICATION_PROMPT = """
You are a research planner. Based on the research goal, identify distinct research areas that need to be explored.

CURRENT DATE: {current_date}

Research Goal: {research_goal}

Your task:
Identify between 2 and 5 DISTINCT research areas/objectives that together will comprehensively address the research goal. Each objective should be:
- Specific and focused
- Non-overlapping with other objectives
- Essential to answering the user's question

Output format (JSON array):
OBJECTIVES: ["objective 1", "objective 2", "objective 3", ...]

Provide 2-5 objectives depending on the complexity of the research goal.
"""

SUB_AGENT_REASONING_PROMPT = """
You are a specialized research sub-agent focused on a specific research objective.

CURRENT DATE: {current_date}

Your Objective: {objective}
Overall Research Goal: {research_goal}
Current Round: {current_round} of {max_rounds}

Previous Findings (from earlier rounds):
{previous_findings}

Your task:
1. Analyze what you've learned so far about YOUR SPECIFIC objective
2. Identify what's still missing for YOUR objective
3. Generate 2-3 targeted search queries to fill the gaps

Output format:
ANALYSIS: [What you know and what's missing about your objective]
REASONING: [Why these searches will help complete your objective]
QUERIES: ["query1", "query2", "query3"]
"""

SUB_AGENT_CONCLUSION_PROMPT = """
You are a specialized research sub-agent. Summarize your findings for your specific objective.

CURRENT DATE: {current_date}

Your Objective: {objective}
Round: {current_round} of {max_rounds}

All content gathered so far:
{all_content}

Your task:
1. Summarize key findings relevant to YOUR objective
2. Assess completeness of your research
3. Decide if you need another round

Output format:
FINDINGS: [Comprehensive summary of what you've learned about your objective]
COMPLETENESS: [How complete is your research on this objective - percentage or assessment]
DECISION: [CONTINUE or FINISH]

Note: If this is round {max_rounds}, you must decide FINISH.
"""

FINAL_SYNTHESIS_PROMPT = """
You are a master synthesizer. You will receive research findings from multiple specialized sub-agents, each focused on a different aspect of the user's question.

CURRENT DATE: {current_date}

User's Original Question: {user_query}
Research Goal: {research_goal}

Sub-Agent Findings:
{all_agent_findings}

Your task:
Synthesize all sub-agent findings into a comprehensive, well-organized knowledge base that enables the chat model to provide a complete answer. Structure the information to:

1. Present a holistic view combining all research areas
2. Highlight connections and relationships between different aspects
3. Include specific facts, data, and sources
4. Note any contradictions or different perspectives
5. Provide actionable insights when relevant

Focus on creating an informative knowledge base rather than directly answering. Include URLs and specific source references.
"""


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class SubAgentFindings:
    """Results from a single sub-agent's research."""
    objective: str
    rounds_completed: int
    findings_summary: str
    sources_consulted: List[str]
    total_content_gathered: int


# ============================================================================
# Main Tool Class
# ============================================================================

class Tools:
    """Deep Research Tool - Parallel Multi-Agent Research System"""

    class Valves(BaseModel):
        exa_api_key: str = Field(
            default="",
            description="Your Exa API key for web search."
        )
        coordinator_model: str = Field(
            default="gpt-4-turbo",
            description="Model for goal definition and objective identification."
        )
        sub_agent_model: str = Field(
            default="gpt-4-turbo",
            description="Model for sub-agent reasoning and research."
        )
        synthesizer_model: str = Field(
            default="gpt-4-turbo",
            description="Model for final synthesis of all findings."
        )
        max_objectives: int = Field(
            default=5,
            description="Maximum number of parallel research objectives (2-5)."
        )
        sub_agent_max_rounds: int = Field(
            default=3,
            description="Maximum research rounds per sub-agent."
        )
        queries_per_round: int = Field(
            default=2,
            description="Number of search queries per sub-agent round."
        )
        urls_per_query: int = Field(
            default=5,
            description="Number of URLs to fetch per query."
        )
        urls_to_crawl: int = Field(
            default=3,
            description="Number of URLs to crawl per query."
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
        Conduct comprehensive research using a parallel multi-agent system.

        Architecture:
        1. AI defines research goal
        2. Identifies 2-5 distinct research objectives
        3. Launches parallel sub-agents (one per objective)
        4. Each sub-agent conducts up to 3 rounds of research with reasoning
        5. Synthesizer combines all findings into comprehensive knowledge base

        Args:
            query: The research question or topic
            __event_emitter__: OpenWebUI event emitter for status updates
            __request__: Request object from OpenWebUI
            __user__: User object from OpenWebUI

        Returns:
            Comprehensive research findings from all sub-agents

        Examples:
            await deep_research("What are the latest developments in quantum computing and their practical applications?")
        """
        if not EXA_AVAILABLE:
            return "❌ Deep research unavailable: exa_py module not installed. Please install with: pip install exa_py"

        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        try:
            current_date = datetime.now().strftime("%Y-%m-%d")

            # ================================================================
            # PHASE 1: Define Research Goal
            # ================================================================
            await _status("🎯 Defining research goal...")

            research_goal = await self._define_research_goal(
                query, current_date, __request__, __user__
            )

            # ================================================================
            # PHASE 2: Identify Research Objectives
            # ================================================================
            await _status("📋 Identifying research objectives...")

            objectives = await self._identify_objectives(
                query, research_goal, current_date, __request__, __user__
            )

            # Limit to max_objectives
            objectives = objectives[:self.valves.max_objectives]

            await _status(f"🚀 Launching {len(objectives)} parallel research agents...")

            # ================================================================
            # PHASE 3: Launch Parallel Sub-Agents
            # ================================================================
            # Create tasks for each sub-agent
            sub_agent_tasks = [
                self._run_sub_agent(
                    objective=obj,
                    research_goal=research_goal,
                    current_date=current_date,
                    agent_id=idx + 1,
                    total_agents=len(objectives),
                    status_func=_status,
                    request=__request__,
                    user=__user__
                )
                for idx, obj in enumerate(objectives)
            ]

            # Run all sub-agents in parallel
            all_findings = await asyncio.gather(*sub_agent_tasks, return_exceptions=True)

            # Filter out exceptions
            valid_findings = []
            for idx, finding in enumerate(all_findings):
                if isinstance(finding, Exception):
                    await _status(f"⚠️ Sub-agent {idx + 1} failed: {str(finding)[:50]}")
                else:
                    valid_findings.append(finding)

            if not valid_findings:
                return "❌ All sub-agents failed. Please try again."

            # ================================================================
            # PHASE 4: Synthesize All Findings
            # ================================================================
            await _status(f"🔄 Synthesizing findings from {len(valid_findings)} agents...")

            final_answer = await self._synthesize_all_findings(
                query=query,
                research_goal=research_goal,
                all_findings=valid_findings,
                current_date=current_date,
                request=__request__,
                user=__user__
            )

            await _status("✓ Research complete", done=True)

            return final_answer

        except Exception as e:
            await _status("", done=True)
            return f"❌ Deep research failed: {str(e)}"

    # ========================================================================
    # Phase 1: Goal Definition
    # ========================================================================

    async def _define_research_goal(
        self, query: str, current_date: str, request, user
    ) -> str:
        """Define the overarching research goal."""
        payload = {
            "model": self.valves.coordinator_model,
            "messages": [
                {
                    "role": "system",
                    "content": GOAL_DEFINITION_PROMPT.format(
                        current_date=current_date, user_query=query
                    )
                },
                {"role": "user", "content": f"Define the research goal for: {query}"},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        response_text = resp["choices"][0]["message"]["content"]

        # Extract GOAL field
        for line in response_text.split("\n"):
            if line.strip().startswith("GOAL:"):
                return line.split("GOAL:", 1)[1].strip()

        # Fallback
        return query

    # ========================================================================
    # Phase 2: Objective Identification
    # ========================================================================

    async def _identify_objectives(
        self, query: str, research_goal: str, current_date: str, request, user
    ) -> List[str]:
        """Identify distinct research objectives."""
        payload = {
            "model": self.valves.coordinator_model,
            "messages": [
                {
                    "role": "system",
                    "content": OBJECTIVE_IDENTIFICATION_PROMPT.format(
                        current_date=current_date, research_goal=research_goal
                    )
                },
                {"role": "user", "content": f"Identify research objectives for: {query}"},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        response_text = resp["choices"][0]["message"]["content"]

        # Extract objectives - try multiple methods
        objectives = []

        # Method 1: Look for JSON array
        for line in response_text.split("\n"):
            if "OBJECTIVES:" in line.upper() and "[" in line:
                try:
                    obj_part = line.split("OBJECTIVES:")[-1].strip()
                    objectives = json.loads(obj_part)
                    break
                except json.JSONDecodeError:
                    pass

        # Method 2: Look for full JSON array in text
        if not objectives:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    objectives = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

        # Method 3: Extract quoted strings
        if not objectives:
            quoted = re.findall(r'"([^"]+)"', response_text)
            if quoted:
                objectives = [q for q in quoted if len(q) > 10]

        # Method 4: Look for numbered list
        if not objectives:
            lines = response_text.split("\n")
            for line in lines:
                if re.match(r'^\s*\d+\.', line):
                    obj = re.sub(r'^\s*\d+\.\s*', '', line).strip()
                    if len(obj) > 10:
                        objectives.append(obj)

        # Fallback
        if not objectives:
            objectives = [
                f"Research aspect 1 of: {query}",
                f"Research aspect 2 of: {query}"
            ]

        return objectives

    # ========================================================================
    # Phase 3: Sub-Agent Research
    # ========================================================================

    async def _run_sub_agent(
        self,
        objective: str,
        research_goal: str,
        current_date: str,
        agent_id: int,
        total_agents: int,
        status_func,
        request,
        user
    ) -> SubAgentFindings:
        """
        Run a single sub-agent that conducts research on a specific objective.

        This sub-agent will:
        1. Conduct up to max_rounds of research
        2. Reason about what information is still needed
        3. Generate targeted search queries
        4. Gather and analyze content
        5. Return comprehensive findings
        """
        await status_func(f"🤖 Agent {agent_id}/{total_agents} starting: {objective[:40]}...")

        all_content = []
        sources = []
        previous_findings = "No previous findings yet."

        for round_num in range(1, self.valves.sub_agent_max_rounds + 1):
            await status_func(
                f"🤖 Agent {agent_id}/{total_agents} - Round {round_num}/{self.valves.sub_agent_max_rounds}"
            )

            # Step 1: Reason about what to search
            queries = await self._sub_agent_reasoning(
                objective=objective,
                research_goal=research_goal,
                previous_findings=previous_findings,
                current_round=round_num,
                max_rounds=self.valves.sub_agent_max_rounds,
                current_date=current_date,
                request=request,
                user=user
            )

            # Step 2: Execute searches in parallel
            search_tasks = [
                self._search_and_get_content(query, sources)
                for query in queries
            ]

            round_content = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Filter out exceptions and empty results
            valid_content = [
                content for content in round_content
                if not isinstance(content, Exception) and content
            ]

            all_content.extend(valid_content)

            # Step 3: Conclude round - summarize and decide if we need more
            if all_content:
                conclusion = await self._sub_agent_conclude_round(
                    objective=objective,
                    all_content="\n\n".join(all_content),
                    current_round=round_num,
                    max_rounds=self.valves.sub_agent_max_rounds,
                    current_date=current_date,
                    request=request,
                    user=user
                )

                # Extract findings and decision
                findings = self._extract_field(conclusion, "FINDINGS:")
                decision = self._extract_field(conclusion, "DECISION:")

                previous_findings = findings

                # If agent decides it's done, stop early
                if decision == "FINISH" or round_num == self.valves.sub_agent_max_rounds:
                    break

        # Final summary for this sub-agent
        final_findings = previous_findings if previous_findings != "No previous findings yet." else "\n\n".join(all_content)

        await status_func(f"✓ Agent {agent_id}/{total_agents} complete")

        return SubAgentFindings(
            objective=objective,
            rounds_completed=round_num,
            findings_summary=final_findings,
            sources_consulted=list(set(sources)),  # Unique sources
            total_content_gathered=sum(len(c) for c in all_content)
        )

    async def _sub_agent_reasoning(
        self,
        objective: str,
        research_goal: str,
        previous_findings: str,
        current_round: int,
        max_rounds: int,
        current_date: str,
        request,
        user
    ) -> List[str]:
        """Sub-agent reasons about what to search next."""
        payload = {
            "model": self.valves.sub_agent_model,
            "messages": [
                {
                    "role": "system",
                    "content": SUB_AGENT_REASONING_PROMPT.format(
                        current_date=current_date,
                        objective=objective,
                        research_goal=research_goal,
                        current_round=current_round,
                        max_rounds=max_rounds,
                        previous_findings=previous_findings[:8000]
                    )
                },
                {"role": "user", "content": "Generate targeted search queries for this round."},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        response_text = resp["choices"][0]["message"]["content"]

        # Extract queries
        queries = []

        # Try to extract JSON array
        for line in response_text.split("\n"):
            if "QUERIES:" in line.upper() and "[" in line:
                try:
                    query_part = line.split("QUERIES:")[-1].strip()
                    queries = json.loads(query_part)
                    break
                except json.JSONDecodeError:
                    pass

        # Try full text JSON
        if not queries:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    queries = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

        # Extract quoted strings
        if not queries:
            queries = re.findall(r'"([^"]+)"', response_text)

        # Fallback
        if not queries:
            queries = [f"{objective} detailed information"]

        return queries[:self.valves.queries_per_round]

    async def _sub_agent_conclude_round(
        self,
        objective: str,
        all_content: str,
        current_round: int,
        max_rounds: int,
        current_date: str,
        request,
        user
    ) -> str:
        """Sub-agent concludes a research round."""
        payload = {
            "model": self.valves.sub_agent_model,
            "messages": [
                {
                    "role": "system",
                    "content": SUB_AGENT_CONCLUSION_PROMPT.format(
                        current_date=current_date,
                        objective=objective,
                        current_round=current_round,
                        max_rounds=max_rounds,
                        all_content=all_content[:16000]
                    )
                },
                {"role": "user", "content": "Summarize findings and decide next steps."},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        return resp["choices"][0]["message"]["content"]

    # ========================================================================
    # Phase 4: Final Synthesis
    # ========================================================================

    async def _synthesize_all_findings(
        self,
        query: str,
        research_goal: str,
        all_findings: List[SubAgentFindings],
        current_date: str,
        request,
        user
    ) -> str:
        """Synthesize findings from all sub-agents."""
        # Format all agent findings
        findings_text = []
        for idx, finding in enumerate(all_findings, 1):
            findings_text.append(
                f"## Sub-Agent {idx} Findings\n"
                f"**Objective:** {finding.objective}\n"
                f"**Rounds Completed:** {finding.rounds_completed}\n"
                f"**Sources Consulted:** {len(finding.sources_consulted)}\n"
                f"**Content Gathered:** {finding.total_content_gathered:,} characters\n\n"
                f"**Findings:**\n{finding.findings_summary}\n\n"
                f"**Sources:**\n" + "\n".join(f"- {src}" for src in finding.sources_consulted[:10])
            )

        all_findings_text = "\n\n---\n\n".join(findings_text)

        payload = {
            "model": self.valves.synthesizer_model,
            "messages": [
                {
                    "role": "system",
                    "content": FINAL_SYNTHESIS_PROMPT.format(
                        current_date=current_date,
                        user_query=query,
                        research_goal=research_goal,
                        all_agent_findings=all_findings_text[:30000]
                    )
                },
                {"role": "user", "content": "Synthesize all findings into a comprehensive knowledge base."},
            ],
            "stream": False,
        }

        resp = await generate_chat_completion(request=request, form_data=payload, user=user)
        return resp["choices"][0]["message"]["content"]

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _search_and_get_content(self, query: str, sources_list: List[str]) -> str:
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

            # Extract content and track sources
            texts = []
            for res in crawled_results.results:
                if res.text and res.text.strip():
                    # Add source to tracking list
                    if hasattr(res, 'url'):
                        sources_list.append(res.url)

                    title = getattr(res, "title", "Unknown Source")
                    url = getattr(res, "url", "")
                    text_summary = ' '.join(res.text.split()[:3000])

                    if text_summary:
                        texts.append(f"**Source:** {title} ({url})\n{text_summary}")

            return "\n\n".join(texts)

        except Exception:
            return ""

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field from formatted text."""
        for line in text.split("\n"):
            if field_name.upper() in line.upper():
                return line.split(":", 1)[1].strip() if ":" in line else ""
        return ""
