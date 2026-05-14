# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "flyte>=2.0.0",
#   "openai>=1.0.0",
# ]
# ///
"""
Chapter 4: Reflection Pattern — Flyte V2 Native Implementation

Reimplements the Producer-Critic reflection loop from the LangChain example
using Flyte V2 primitives only (no LangGraph, no LangChain).

Flyte V2 features demonstrated:
  - Typed dataclasses as serializable agent memory (ConversationMemory)
  - @flyte.trace for per-LLM-call checkpointing visible in the Flyte UI
  - flyte.report for HTML iteration reports streamed live to the UI
  - ReusePolicy to keep containers warm across iterative LLM calls
  - Secret injection via flyte.Secret (no hardcoded credentials)
  - Cache(behavior="disable") on non-deterministic LLM tasks
  - retries + timeout for resilience against transient API failures

Run remotely:
    flyte run chapter_04_reflection.py reflection_env.reflection_task \\
        --task_prompt "$(cat prompts/factorial.txt)" --max_iterations 3

Run locally (no Flyte tracking):
    python chapter_04_reflection.py
"""

import os
from dataclasses import dataclass
from datetime import timedelta

from openai import AsyncOpenAI, OpenAI
import flyte
import flyte.report


# ---------------------------------------------------------------------------
# Data models — typed agent memory
# ---------------------------------------------------------------------------


@dataclass
class Message:
    """A single dialogue turn in the conversation history."""

    role: str     # "user" | "assistant"
    content: str


@dataclass
class ConversationMemory:
    """
    Immutable-style conversation history passed between Flyte task invocations.

    Design rationale vs. LangChain:
      LangChain stores message history as in-process Python objects tied to a
      specific chain instance. Here, the full history is a plain serializable
      dataclass so Flyte can:
        - Store it durably in object storage between task retries
        - Display it as structured output in the Flyte UI
        - Let any downstream task inspect the full producer/critic dialogue

    Immutability pattern: .append() returns a new object so callers reason
    about state transitions functionally — each iteration's memory snapshot is
    distinct, matching Flyte's data-lineage model.
    """

    messages: list[Message] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.messages is None:
            self.messages = []

    def append(self, role: str, content: str) -> ConversationMemory:
        """Return a *new* ConversationMemory with the message appended."""
        return ConversationMemory(messages=self.messages + [Message(role, content)])

    def to_api_format(self) -> list[dict]:
        """Convert to the OpenAI messages API format."""
        return [{"role": m.role, "content": m.content} for m in self.messages]


@dataclass
class ReflectionResult:
    """Final typed output of the reflection workflow."""

    final_code: str
    iterations_used: int
    converged: bool           # True when the critic approved with CODE_IS_PERFECT
    history: ConversationMemory


# ---------------------------------------------------------------------------
# TaskEnvironment — shared image, secrets, and container reuse
# ---------------------------------------------------------------------------

_image = (
    flyte.Image.from_debian_base(name="reflection-agent", python_version=(3, 12))
    .with_pip_packages("openai>=1.0.0").with_env_vars(OPENAI_API_KEY=os.environ['OPENAI_API_KEY'])  # for local testing; overridden by secret in production
)

reflection_env = flyte.TaskEnvironment(
    name="reflection_llm",
    image=_image,
    resources=flyte.Resources(cpu="1", memory="2Gi"),
   # secrets=[
        # Create the secret once via CLI before running:
        #   flyte create secret openai_api_key <your-key>
    #    flyte.Secret(key="OPENAI_API_KEY", as_env_var="OPENAI_API_KEY"),
    #],
    # ReusePolicy: keeps containers warm across multiple LLM calls in the loop.
    # A cold-start cost is paid only for the first iteration; subsequent
    # producer + critic calls reuse the same warm pod — critical for loops
    # that may run 3–10 iterations.
    reusable=flyte.ReusePolicy(
        replicas=(1, 4),
        concurrency=4,          # async def allows multiplexing per pod
        scaledown_ttl=timedelta(minutes=5),
        idle_ttl=timedelta(minutes=10),
    ),
)


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

PRODUCER_SYSTEM = """\
You are an expert Python developer.
Produce clean, well-documented, idiomatic Python code.
Return ONLY the raw Python source — no prose, no markdown fences.\
"""

CRITIC_SYSTEM = """\
You are a senior software engineer conducting a meticulous code review.
Evaluate the submitted code strictly against the stated task requirements.
Check for: correctness, edge case coverage, docstring completeness,
PEP 8 compliance, and robust error handling.

If the code satisfies ALL requirements with zero issues, respond with exactly:
  CODE_IS_PERFECT

Otherwise, respond ONLY with a concise bulleted list of actionable critique
points. Do not rewrite the code — critique only.\
"""


# ---------------------------------------------------------------------------
# @flyte.trace helpers — each LLM call becomes a named checkpoint in the UI
#
# Why traces matter for resilience:
#   Without traces, a pod crash mid-loop restarts the entire task from iteration 0,
#   consuming tokens and time. With @flyte.trace, each successful LLM call is
#   checkpointed. On retry, execution resumes from the last completed checkpoint
#   rather than the beginning — reducing wasted cost proportional to loop depth.
# ---------------------------------------------------------------------------


@flyte.trace
async def _produce(
    memory: ConversationMemory,
    iteration: int,
) -> str:
    """
    Traced producer call.
    Iteration 0 → initial code generation from the task prompt.
    Iteration N → refinement guided by the critique already in memory.
    """
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    messages = memory.to_api_format()
    if iteration > 0:
        messages.append({
            "role": "user",
            "content": "Refine the code to fully address all critique points listed above.",
        })

    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[{"role": "system", "content": PRODUCER_SYSTEM}] + messages,
    )
    return response.choices[0].message.content


@flyte.trace
async def _critique(task_prompt: str, code: str) -> str:
    """
    Traced critic call.
    The critic receives only (task_prompt, code) — no producer history — to
    preserve the separation-of-concerns design from the chapter: the critic
    evaluates output objectively, without bias from the producer's context.
    """
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = await client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[{"role": "system", "content": CRITIC_SYSTEM}] + [
            {
                "role": "user",
                "content": (
                    f"Original task requirements:\n{task_prompt}\n\n"
                    f"Code to review:\n{code}"
                ),
            }
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main reflection task
# ---------------------------------------------------------------------------


@reflection_env.task(
    retries=3,
    timeout=timedelta(minutes=30),
    # LLM outputs are non-deterministic; caching would return stale results.
    cache=flyte.Cache(behavior="disable"),
    # report=True enables the HTML tab in the Flyte UI for live iteration progress.
    report=True,
)
async def reflection_task(
    task_prompt: str,
    max_iterations: int = 3,
) -> ReflectionResult:
    """
    Producer-Critic reflection loop, Flyte V2 native.

    Memory flow:
      1. Seed ConversationMemory with the task prompt as the first user turn.
      2. Producer reads full memory → generates code → appended to memory as assistant turn.
      3. Critic reads (task_prompt, code) independently → returns critique or CODE_IS_PERFECT.
      4. If imperfect, critique is appended to memory as a user turn.
      5. On the next iteration, the producer sees: prompt → code → critique → refine prompt.
      6. Repeat until CODE_IS_PERFECT or max_iterations reached.

    This memory structure faithfully mirrors the LangChain example's message_history
    but as a typed, serializable dataclass — inspectable and reproducible across retries.
    """
    memory = ConversationMemory().append("user", task_prompt)

    current_code = ""
    converged = False
    report_sections: list[str] = []
    final_iteration = 0

    for i in range(max_iterations):
        final_iteration = i
        label = f"Iteration {i + 1} / {max_iterations}"

        # ── Producer step ────────────────────────────────────────────────────
        current_code = await _produce(memory=memory, iteration=i)

        # Record the refinement prompt in memory (only from iteration 1 onward)
        if i > 0:
            memory = memory.append(
                "user",
                "Refine the code to fully address all critique points listed above.",
            )
        memory = memory.append("assistant", current_code)

        # ── Critic step ──────────────────────────────────────────────────────
        critique = await _critique(task_prompt=task_prompt, code=current_code)

        status = "APPROVED" if "CODE_IS_PERFECT" in critique else "NEEDS IMPROVEMENT"

        # ── Live report update ───────────────────────────────────────────────
        report_sections.append(
            f"<section>"
            f"<h2>{label} — <span style='color:{'green' if converged else 'orange'}'>{status}</span></h2>"
            f"<h3>Producer Output</h3>"
            f"<pre style='background:#f4f4f4;padding:1em;border-radius:4px'>"
            f"<code>{_html_escape(current_code)}</code></pre>"
            f"<h3>Critic Feedback</h3>"
            f"<pre style='background:#fff8e1;padding:1em;border-radius:4px'>"
            f"{_html_escape(critique)}</pre>"
            f"</section><hr/>"
        )
        await flyte.report.replace.aio(_render_report(report_sections, i + 1, status))
        await flyte.report.flush.aio()

        # ── Stopping condition ────────────────────────────────────────────────
        if "CODE_IS_PERFECT" in critique:
            converged = True
            break

        # Append critique to memory so the next producer sees it
        memory = memory.append(
            "user",
            f"Critique from senior engineer (iteration {i + 1}):\n{critique}",
        )

    return ReflectionResult(
        final_code=current_code,
        iterations_used=final_iteration + 1,
        converged=converged,
        history=memory,
    )


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _render_report(sections: list[str], completed: int, latest_status: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
           padding: 1.5em; max-width: 900px; margin: auto; }}
    h1   {{ border-bottom: 2px solid #333; padding-bottom: .4em; }}
    pre  {{ white-space: pre-wrap; word-break: break-word; font-size: .85em; }}
    hr   {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
  </style>
</head>
<body>
  <h1>Reflection Pattern — Live Execution Report</h1>
  <p>
    Completed iterations: <strong>{completed}</strong> &nbsp;|&nbsp;
    Latest status: <strong>{latest_status}</strong>
  </p>
  {"".join(sections)}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Example task prompts
# ---------------------------------------------------------------------------

FACTORIAL_PROMPT = """\
Create a Python function named `calculate_factorial` that:
1. Accepts a single integer `n` as input.
2. Calculates and returns its factorial (n!).
3. Includes a clear, complete docstring.
4. Handles the edge case: factorial of 0 is 1.
5. Raises ValueError with a descriptive message for negative inputs.
"""

BINARY_SEARCH_PROMPT = """\
Create a Python function named `binary_search` that:
1. Accepts a sorted list of integers and a target integer.
2. Returns the index of the target if found, or -1 if not present.
3. Implements the binary search algorithm (not a linear scan).
4. Includes a docstring with parameter descriptions and return value.
5. Raises TypeError if the input list is not sorted.
"""


# ---------------------------------------------------------------------------
# Local entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        print("Running Reflection Pattern locally (no Flyte tracking).")
        print("=" * 60)

        result = await reflection_task(
            task_prompt=FACTORIAL_PROMPT,
            max_iterations=3,
        )

        print(f"\nConverged: {result.converged}")
        print(f"Iterations used: {result.iterations_used}")
        print(f"\n{'='*60}")
        print("FINAL CODE")
        print("=" * 60)
        print(result.final_code)

        print(f"\n{'='*60}")
        print("CONVERSATION MEMORY SUMMARY")
        print("=" * 60)
        for i, msg in enumerate(result.history.messages):
            snippet = msg.content[:120].replace("\n", " ")
            print(f"  [{i}] {msg.role.upper():10s} → {snippet}...")

    asyncio.run(main())
