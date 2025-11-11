# Deep Research Multi-Agent Architecture

This document explains the parallel multi-agent architecture used in the `deep_research.py` tool.

## 🎯 Overview

The deep research tool uses a sophisticated parallel multi-agent system where multiple specialized sub-agents research different aspects of a question simultaneously, then a master synthesizer combines their findings.

## 🏗️ Architecture Comparison

### Old Architecture (Sequential/Iterative)
```
User Query
   ↓
Define Goal → Set Objectives
   ↓
Iteration 1 → Generate Queries → Search All → Summarize
   ↓
Iteration 2 → Generate Queries → Search All → Summarize
   ↓
Final Synthesis
```

**Limitations:**
- Sequential processing (slower)
- All queries compete for the same research thread
- Less specialized research per topic
- Single point of failure

### New Architecture (Parallel Multi-Agent)
```
User Query
   ↓
Coordinator: Define Goal
   ↓
Coordinator: Identify 2-5 Objectives
   ↓
   ├─────────┬─────────┬─────────┬─────────┐
   │         │         │         │         │
Agent 1   Agent 2   Agent 3   Agent 4   Agent 5
(Obj 1)   (Obj 2)   (Obj 3)   (Obj 4)   (Obj 5)
   │         │         │         │         │
Round 1   Round 1   Round 1   Round 1   Round 1
 ├Reason   ├Reason   ├Reason   ├Reason   ├Reason
 ├Query    ├Query    ├Query    ├Query    ├Query
 └Search   └Search   └Search   └Search   └Search
   │         │         │         │         │
Round 2   Round 2   Round 2   Round 2   Round 2
 ├Reason   ├Reason   ├Reason   ├Reason   ├Reason
 ├Query    ├Query    ├Query    ├Query    ├Query
 └Search   └Search   └Search   └Search   └Search
   │         │         │         │         │
Round 3   Round 3   Round 3   Round 3   Round 3
 ├Reason   ├Reason   ├Reason   ├Reason   ├Reason
 ├Query    ├Query    ├Query    ├Query    ├Query
 └Search   └Search   └Search   └Search   └Search
   │         │         │         │         │
Findings  Findings  Findings  Findings  Findings
   │         │         │         │         │
   └─────────┴─────────┴─────────┴─────────┘
                       ↓
              Master Synthesizer
                       ↓
         Comprehensive Knowledge Base
```

**Advantages:**
- **Parallel execution** - All agents run simultaneously
- **Specialized focus** - Each agent focuses on one specific objective
- **Fault tolerance** - One agent failure doesn't crash the system
- **Scalable** - 2-5 agents based on question complexity
- **Deeper research** - Each objective gets dedicated investigation

## 📋 Four Phases

### Phase 1: Goal Definition
**Actor:** Coordinator Model
**Task:** Analyze user question and define research goal

**Input:**
```
User: "What are the latest developments in quantum computing
       and their practical applications?"
```

**Output:**
```
GOAL: Investigate recent quantum computing breakthroughs and
      identify real-world applications across industries
SCOPE: Include hardware advances, algorithmic improvements,
       and commercial implementations from 2023-2025
EXPECTED_DEPTH: Comprehensive
```

---

### Phase 2: Objective Identification
**Actor:** Coordinator Model
**Task:** Break down goal into 2-5 distinct research areas

**Output:**
```json
OBJECTIVES: [
  "Recent hardware breakthroughs in quantum computing (qubits, error correction)",
  "Algorithmic advances and quantum software development",
  "Commercial applications in cryptography and security",
  "Industry applications (pharma, finance, materials science)",
  "Challenges and timeline for practical quantum advantage"
]
```

Each objective becomes a specialized sub-agent mission.

---

### Phase 3: Parallel Sub-Agent Research

**Each Sub-Agent:**
1. Receives one specific objective
2. Conducts up to 3 rounds of research
3. Reasons about what information is still needed
4. Generates targeted queries
5. Searches and gathers content
6. Summarizes findings

**Example Sub-Agent 1 (Hardware):**

**Round 1:**
```
ANALYSIS: Need to understand recent qubit improvements
REASONING: Start with general hardware advances, then dive into specifics
QUERIES: [
  "quantum computing hardware breakthroughs 2024 2025",
  "superconducting qubit improvements error rates"
]
→ Search & gather content
```

**Round 2:**
```
ANALYSIS: Found info on superconducting qubits, need info on other types
REASONING: Explore trapped ion, topological, and photonic qubits
QUERIES: [
  "trapped ion quantum computers recent advances",
  "topological qubits Microsoft 2024"
]
→ Search & gather content
```

**Round 3:**
```
ANALYSIS: Have comprehensive hardware overview, need error correction specifics
REASONING: Error correction is crucial for practical quantum computing
QUERIES: [
  "quantum error correction surface codes 2024",
  "logical qubit implementations Google IBM"
]
→ Search & gather content
DECISION: FINISH (comprehensive coverage achieved)
```

**Meanwhile, all other sub-agents are running in parallel...**

---

### Phase 4: Master Synthesis

**Actor:** Synthesizer Model
**Input:** Findings from all sub-agents

```markdown
## Sub-Agent 1 Findings
Objective: Recent hardware breakthroughs...
Rounds Completed: 3
Sources Consulted: 15
Findings: [Comprehensive hardware summary with sources]

## Sub-Agent 2 Findings
Objective: Algorithmic advances...
Rounds Completed: 3
Sources Consulted: 12
Findings: [Comprehensive algorithm summary with sources]

## Sub-Agent 3 Findings
Objective: Commercial applications in cryptography...
Rounds Completed: 2
Sources Consulted: 10
Findings: [Cryptography applications summary with sources]

[etc...]
```

**Task:** Synthesize into holistic knowledge base

**Output:**
```markdown
# Comprehensive Research: Quantum Computing Developments & Applications

## Hardware Advances
[Synthesized information from Sub-Agent 1]
- Recent breakthroughs in qubit coherence times
- Error correction achievements
- Connections to practical applications

## Algorithmic Progress
[Synthesized information from Sub-Agent 2]
- New quantum algorithms
- Software frameworks
- Integration with hardware advances

## Practical Applications
[Synthesized information from Sub-Agents 3-5]
- Cryptography and security uses
- Industry-specific applications
- Current limitations and timeline
- Cross-connections between hardware and applications

## Sources
[All unique sources from all agents, organized by topic]
```

## 🔄 Execution Flow

```python
# Simplified code flow
async def deep_research(query):
    # Phase 1: Define goal
    goal = await coordinator.define_goal(query)

    # Phase 2: Identify objectives
    objectives = await coordinator.identify_objectives(goal)  # Returns 2-5 objectives

    # Phase 3: Launch parallel sub-agents
    tasks = [
        run_sub_agent(obj) for obj in objectives
    ]
    all_findings = await asyncio.gather(*tasks)  # Run in parallel!

    # Phase 4: Synthesize
    final = await synthesizer.combine(all_findings)
    return final
```

## 🤖 Sub-Agent Internal Loop

```python
async def run_sub_agent(objective):
    findings = []

    for round in range(1, max_rounds + 1):
        # Step 1: Reason about what to search
        queries = await reason_about_next_searches(
            objective, previous_findings
        )

        # Step 2: Execute searches in parallel
        search_tasks = [search(q) for q in queries]
        content = await asyncio.gather(*search_tasks)

        findings.extend(content)

        # Step 3: Summarize and decide if done
        conclusion = await summarize_round(findings)

        if conclusion.decision == "FINISH":
            break

    return SubAgentFindings(
        objective=objective,
        findings_summary=conclusion.summary,
        sources=sources,
        rounds_completed=round
    )
```

## 📊 Performance Characteristics

| Metric | Sequential | Parallel Multi-Agent |
|--------|-----------|---------------------|
| **Time Complexity** | O(iterations × queries) | O(max_rounds) * |
| **Coverage** | Broad but shallow | Deep and specialized |
| **Parallelism** | None | Up to 5 simultaneous agents |
| **Fault Tolerance** | Single point of failure | Graceful degradation |
| **Scalability** | Limited by iterations | Scales with objectives |

\* Actual time is O(max_rounds) because all agents run in parallel

## 🎛️ Configuration

### Coordinator Model
```python
coordinator_model: "gpt-4-turbo"  # For strategic thinking
```
- Defines research goals
- Identifies research objectives
- Requires strategic reasoning capability

### Sub-Agent Model
```python
sub_agent_model: "gpt-4-turbo"  # For focused research
```
- Conducts specialized research
- Reasons about information gaps
- Generates targeted queries

### Synthesizer Model
```python
synthesizer_model: "gpt-4-turbo"  # For holistic synthesis
```
- Combines all sub-agent findings
- Creates comprehensive knowledge base
- Identifies connections across objectives

### Parallelism
```python
max_objectives: 5  # 2-5 parallel sub-agents
sub_agent_max_rounds: 3  # Rounds per sub-agent
queries_per_round: 2  # Queries per round
```

## 🔍 Example Execution

**Query:** "How is AI impacting healthcare in 2025?"

**Phase 1 - Goal:**
```
Investigate current AI applications in healthcare and their
impact on patient outcomes, diagnostics, and medical workflows
```

**Phase 2 - Objectives:**
1. AI in medical diagnostics and imaging
2. AI in drug discovery and development
3. AI in personalized medicine and treatment planning
4. AI in hospital operations and workflow optimization
5. Regulatory and ethical considerations

**Phase 3 - Parallel Research:**
- Agent 1-5 launch simultaneously
- Each conducts 3 rounds (or until satisfied)
- Total: 5 agents × 3 rounds × 2 queries = 30 searches
- Time: Same as 3 sequential rounds (parallelized)

**Phase 4 - Synthesis:**
- Combines findings from all 5 agents
- Creates holistic view of AI in healthcare
- Highlights cross-connections
- Provides comprehensive knowledge base

## 🎯 When to Use This Tool

**Ideal for:**
- Complex, multi-faceted questions
- Research requiring multiple perspectives
- Topics with distinct sub-domains
- Questions needing comprehensive coverage

**Examples:**
- "Analyze the global impact of climate change policies"
- "Compare quantum computing approaches and their trade-offs"
- "Evaluate AI safety concerns across different domains"
- "Research renewable energy adoption worldwide"

**Not ideal for:**
- Simple factual queries → Use `web_search` instead
- Single-URL content extraction → Use `crawl_url` instead
- Questions with single clear answer → Use `web_search` instead

## 🚀 Performance Benefits

1. **Speed**: Parallel execution means 5 agents complete in the same time as 1
2. **Depth**: Each objective gets dedicated, focused research
3. **Coverage**: Multiple perspectives ensure comprehensive understanding
4. **Quality**: Specialized focus produces better insights per topic
5. **Resilience**: One agent failure doesn't compromise entire research

## 🔧 Technical Implementation

**Key Technologies:**
- `asyncio.gather()` for parallel execution
- `@dataclass` for structured findings
- Exception handling with `return_exceptions=True`
- Independent agent contexts
- Source tracking across agents

**Error Handling:**
```python
# Graceful degradation
all_findings = await asyncio.gather(*tasks, return_exceptions=True)

valid_findings = [
    f for f in all_findings
    if not isinstance(f, Exception)
]

# Continue with valid findings even if some agents failed
```

---

## 📚 Further Reading

- See `deep_research.py` for full implementation
- See `README.md` for usage examples
- See configuration valves for customization options
