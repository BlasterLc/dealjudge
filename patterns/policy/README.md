# `#policy`: a typed question gates a tool call

One file, `policy_gate.py`. It needs `strands-agents` and a running Strands Decider 2B server.
([Versión en español](README.es.md))

## What it does

Before a watched tool runs, the gate asks Decider your **typed questions** about the situation, in
one round trip, and passes the answers to **your own plain-Python function** that returns
`("proceed" | "deny" | "guide", message)`. The gate maps that to the SDK's `Proceed`, `Deny` or
`Guide`. The model measures; your code decides.

Use it when a tool call should depend on a judgement that a 2B model can make from text
(is this a real discount, is this request urgent, is this input trusted) and where you want the
final rule to be auditable code, not another prompt.

## The typed question

A question is data, not a prompt you tune per call:

```python
{"type": "choice",                       # "choice" (pick one label) or "noul" (yes/no)
 "instructions": "What level of offer is this?",
 "criteria": {"good": "10-25 % under the median", "very_good": "25-40 % under the median"}}
```

`choice` answers `{"choice": label, "probabilities": {...}, "confidence": float}`;
`noul` answers `{"noul": P(true)}`.

## Wiring

```python
from strands import Agent
from policy_gate import PolicyGate, DeciderHTTP

gate = PolicyGate(
    questions=QUESTIONS,
    render=lambda event: f"tool={event.tool_use['name']} input={event.tool_use['input']}",
    decide=my_rule,                 # answers -> ("proceed" | "deny" | "guide", message)
    client=DeciderHTTP(),           # DECIDER_URL, default http://127.0.0.1:8000
    tools={"send_alert"},           # None watches every tool
)
agent = Agent(model=..., tools=[send_alert], interventions=[gate])
```

If the server does not answer, or `decide` raises, the gate denies the call: an unjudged call
does not run.

## Things we learned the hard way (measure these on your data)

- **Point the question at the figure.** Asking "is this discount real?" got 53 % on our data
  (Spanish prompt, dev split); asking "look at the line `real discount vs median`: is it 10 % or more?" got 94 %. Put the
  numbers in the state text and tell the model which line to read.
- **Do not make it do arithmetic.** A question that needs a price compared with a cap *and* a
  level compared with a minimum was answered correctly less often than chance (37-41 %). Compute
  that in code and keep Decider for the reading.
- **One language end to end.** The state, the questions and the option names must be in the same language;
  do not mix a Spanish state with English labels.
- **`confidence` is not a probability.** For `choice` questions it lives on a low scale
  (a correct pick at P=0.30 reported 0.13). Fit your threshold on a dev split, with a rule that
  only gives a decisive answer when it is right more than half the time.

See how Dealjudge uses it in `src/dealjudge/handler.py` and `src/dealjudge/policy.py`.
