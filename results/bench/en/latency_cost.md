# Latency and cost, en (simulated states, dev seed 101, 70 cases)

| | Decider 2B (local GPU) | claude-haiku-4-5-20251001-v1:0 (Bedrock) |
|---|---|---|
| median, wall clock (ms) | 277.9 | 940.3 |
| p95, wall clock (ms) | 336.2 | 2493.7 |
| max, wall clock (ms) | 362.3 | 2493.7 |
| failed calls (LLM: no retries) | 0 of 70 | 52 of 70 |
| API cost per 1,000 decisions (USD) | 0 | 0.5307 |
| tokens per decision (in / out) | n/a | 383 / 29 |

Decider's cost is your own GPU time (not counted here). Both ask the same three questions on the same state.
The LLM latency is for calls that succeeded and includes the network; Decider ran on the same machine as this script.
Failed LLM calls are Bedrock rate limits (ThrottlingException) on this account at a sequential pace; with default retries they are retried and cost seconds instead.
