# Evaluation (simulated data)

All figures are on **simulated** offers (210 test cases, seed 303); the confidence threshold (0.1) was fixed on a separate dev split (seed 101). Truth is computed from each price series by `truth_for()`; see `dealjudge/generator.py`.

| Metric | Decider + rule | cyber-watch rule | LLM |
|---|---|---|---|
| Alert vs silence accuracy | 0.943 | 0.814 | 0.938 |
| 3-way action accuracy | 0.943 | 0.69 | 0.933 |
| Real/fake accuracy | 1.0 | n/a | 0.962 |
| Offer level accuracy | 0.79 | n/a | 0.919 |
| Latency median / p95 (ms) | 484.405 / 602.79 | ~0 | 573.5 / 685.0 |
| API cost (USD) | 0 (local) | 0 | 0.1063 |

Decider answers decisively on 86% of offers and is right 93% of the time on those; the rest get a warning.

Decider's own answer to "does it fit this user?" was right 44% of the time, so that comparison (price vs cap, level vs minimum) is done in code.

Failures: Decider 0, LLM 8.

## Alert accuracy by scenario

| Scenario | n | Decider | Rule | LLM |
|---|---|---|---|---|
| inflated_spike | 30 | 1.0 | 0.933 | 0.967 |
| genuine_drop | 30 | 1.0 | 0.567 | 0.967 |
| normal_fluctuation | 30 | 1.0 | 1.0 | 0.867 |
| recurring_sale | 30 | 1.0 | 0.967 | 0.933 |
| short_history | 30 | 1.0 | 0.867 | 1.0 |
| edge_10 | 30 | 0.6 | 0.6 | 0.833 |
| edge_25 | 30 | 1.0 | 0.767 | 1.0 |

## Calibration (expected calibration error, lower is better)

- is_real: 0.134
- level: 0.374
- level_prob: 0.257
