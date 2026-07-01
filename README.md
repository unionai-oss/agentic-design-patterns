# Agentic Design Patterns on Flyte V2
This repo implements code examples from Antonio Gulli's [Agentic Design Patterns](https://link.springer.com/book/10.1007/978-3-032-01402-3) book with Flyte V2.

The repo ships with the [configuration](./.flyte/config.yaml) so you can run all examples in the [Flyte Devbox](https://www.union.ai/docs/v2/union/user-guide/run-modes/running-devbox/).

## Built on Flyte's agentic primitives

Where it makes the pattern clearer, the notebooks use Flyte v2's first-class agent toolkit (`flyte.ai.agents`) instead of a hand-rolled `@flyte.trace` tool loop:

- **`Agent`** — a batteries-included LLM ↔ tool loop with declarative `@tool`s, MCP servers, optional `MemoryStore`, HITL approval, and a typed `AgentResult`. Sync `agent.run(...)`; async `await agent.run.aio(...)`. Used in routing (2), tool-use (5), planning (6), multi-agent (7), RAG (14), inter-agent (15), prioritization (20); subclassed to wrap the loop in goal-setting (11), reasoning (17), and guardrails (18).
- **`MemoryStore`** — a session-keyed transcript + path-addressed artifacts backed by `flyte.io.Dir`, with optimistic concurrency (`expected_sha`). Memory management (8).
- **`MCPServerSpec`** — connect a real MCP server over stdio/HTTP and surface its tools transparently. Model Context Protocol (10).
- **`@tool(requires_approval=True)`** — a human-in-the-loop approval gate via `flyteplugins-hitl`. Human-in-the-loop (13), guardrails (18).
- **`CodeModeAgent` + `flyte.sandbox.create` / `orchestrate_local`** — run LLM-generated code in fresh, isolated sandboxes. Learning and adaptation (9).

The remaining patterns (prompt chaining, parallelization, reflection, exception handling, resource-aware optimization, evaluation, exploration) stay on plain `@env.task` composition — each notebook ends with a short note on *why* the harness isn't a win there.

## Part One: Core Patterns

| # | Pattern | Description |
|---|---------|-------------|
| 1 | [Prompt Chaining](01-Part_One/1-prompt-chaining.ipynb) | Chain multiple LLM calls where each output feeds the next |
| 2 | [Routing](01-Part_One/2-routing.ipynb) | Classify inputs and direct them to specialized handlers |
| 3 | [Parallelization](01-Part_One/3-parallelization.ipynb) | Run independent tasks concurrently and aggregate results |
| 4 | [Reflection](01-Part_One/4-reflection.ipynb) | Producer-Critic loop for iterative self-improvement |
| 5 | [Tool Use](01-Part_One/5-tool-use.ipynb) | Autonomous function calling against external APIs and services |
| 6 | [Planning](01-Part_One/6-planning.ipynb) | Decompose complex goals into structured, executable steps |
| 7 | [Multi-Agent Collaboration](01-Part_One/7-multi-agent-collaboration.ipynb) | Cooperative ensemble of specialized agents |

## Part Two: Memory & Adaptation

| # | Pattern | Description |
|---|---------|-------------|
| 8 | [Memory Management](02-Part_Two/8-memory-management.ipynb) | Short- and long-term memory across interactions |
| 9 | [Learning and Adaptation](02-Part_Two/9-learning-and-adaptation.ipynb) | Evolutionary evaluate → select → mutate loop |
| 10 | [Model Context Protocol (MCP)](02-Part_Two/10-model-context-protocol.ipynb) | Standardized tool discovery and invocation for LLMs |
| 11 | [Goal Setting and Monitoring](02-Part_Two/11-goal-setting.ipynb) | Generate → evaluate → refine loop toward a defined objective |

## Part Three: Reliability

| # | Pattern | Description |
|---|---------|-------------|
| 12 | [Exception Handling and Recovery](03-Part_Three/12-exception-handling.ipynb) | Layered resilience against tool failures and invalid responses |
| 13 | [Human-in-the-Loop](03-Part_Three/13-human-in-the-loop.ipynb) | Strategic human judgment injection for high-risk decisions |
| 14 | [Knowledge Retrieval (RAG)](03-Part_Three/14-rag.ipynb) | Retrieval-Augmented Generation for grounded, up-to-date responses |

## Part Four: Advanced Patterns

| # | Pattern | Description |
|---|---------|-------------|
| 15 | [Inter-Agent Communication (A2A)](04-Part_Four/15-inter-agent-communication.ipynb) | Agent-to-agent delegation and collaboration across frameworks |
| 16 | [Resource-Aware Optimization](04-Part_Four/16-resource-aware-optimization.ipynb) | Dynamic model/tool routing by cost and complexity |
| 17 | [Reasoning Techniques (Deep Research)](04-Part_Four/17-reasoning.ipynb) | Generate → research → reflect → finalize research loop |
| 18 | [Guardrails / Safety Patterns](04-Part_Four/18-guardrails.ipynb) | Policy-compliance screening before primary AI processing |
| 19 | [Evaluation and Monitoring](04-Part_Four/19-evaluation-and-monitoring.ipynb) | Token tracking, latency monitoring, and output quality metrics |
| 20 | [Prioritization](04-Part_Four/20-prioritization.ipynb) | Multi-criteria task ranking for autonomous next-action selection |
| 21 | [Exploration and Discovery](04-Part_Four/21-exploration-and-discovery.ipynb) | Multi-agent scientific research with specialized phase agents |
