"""Reusable decision pattern: a typed question gates a tool call (``#policy``).

Drop this one file into a Strands agent (it needs only ``strands-agents`` and a running
Decider server). Before a watched tool runs, the gate:

1. renders the situation as text (``render``),
2. asks Decider your typed questions in one round trip,
3. hands the answers to YOUR plain-Python ``decide`` function, which returns
   ``("proceed" | "deny" | "guide", message)``.

The model is never the gate: Decider measures, ``decide`` decides, and you can replay a
logged answer against any rule or threshold later.

Wiring (the whole of it)::

    from strands import Agent
    from policy_gate import PolicyGate, DeciderHTTP

    gate = PolicyGate(
        questions={"urgency": {"type": "choice", "instructions": "How urgent is this?",
                               "criteria": {"low": "can wait", "high": "needs action now"}}},
        render=lambda event: f"tool={event.tool_use['name']} input={event.tool_use['input']}",
        decide=lambda answers: ("proceed", "") if answers["urgency"]["choice"] == "high"
                               else ("deny", "Not urgent enough to interrupt anyone."),
        client=DeciderHTTP(),            # http://127.0.0.1:8000 or DECIDER_URL
        tools={"send_alert"},            # watch only these tools (None = all)
    )
    agent = Agent(model=..., tools=[send_alert], interventions=[gate])

Answer shapes: a ``noul`` question answers ``{"noul": P(true)}``; a ``choice`` question answers
``{"choice": label, "probabilities": {...}, "confidence": float}``. Measure the confidence
scale on your own data before using it as a threshold: it is not a plain probability.
"""

from __future__ import annotations

import asyncio
import json
import os
import urllib.request
from collections.abc import Callable, Collection, Mapping
from typing import Any

from strands.interventions import Deny, Guide, InterventionHandler, Proceed

Decision = tuple[str, str]  # ("proceed" | "deny" | "guide", message)


class DeciderHTTP:
    """Minimal synchronous client: POST /v1/systemone, returns the answers under your question keys."""

    def __init__(self, url: str | None = None, timeout: float = 120.0) -> None:
        self.url = (url or os.environ.get("DECIDER_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout

    def ask(self, state: str, questions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        body = json.dumps({"state": state, "questions": dict(questions)}, ensure_ascii=False).encode()
        request = urllib.request.Request(
            f"{self.url}/v1/systemone", data=body, headers={"content-type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read())["answers"]


class PolicyGate(InterventionHandler):
    name = "policy-gate"

    def __init__(
        self,
        questions: Mapping[str, Mapping[str, Any]],
        render: Callable[[Any], str],
        decide: Callable[[dict[str, Any]], Decision],
        client: Any,
        tools: Collection[str] | None = None,
    ) -> None:
        self._questions, self._render, self._decide, self._client = questions, render, decide, client
        self._tools = set(tools) if tools is not None else None

    async def before_tool_call(self, event: Any, **kwargs: Any) -> Proceed | Deny | Guide:
        tool_use = getattr(event, "tool_use", None) or {}
        if self._tools is not None and tool_use.get("name") not in self._tools:
            return Proceed()
        try:
            answers = await asyncio.to_thread(self._client.ask, self._render(event), self._questions)
            action, message = self._decide(answers)
        except Exception:  # fail closed: an unanswered or unreadable gate does not let the call run
            return Deny("The policy gate could not judge this call.")
        if action == "proceed":
            return Proceed()
        if action == "guide":
            return Guide(feedback=message)
        return Deny(message)
