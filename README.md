# agentic-design-patterns
This repo implements code examples from Antonio Giulli's [Agentic Design Patterns](https://link.springer.com/book/10.1007/978-3-032-01402-3) book with Flyte V2

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
