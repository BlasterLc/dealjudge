# Evaluation (simulated data)

All figures are on **simulated** offers (210 test cases, seed 303); the confidence threshold (0.1) was fixed on a separate dev split (seed 101). Truth is computed from each price series by `truth_for()`; see `dealjudge/generator.py`.

| Metric | Decider + rule | cyber-watch rule | LLM |
|---|---|---|---|
| Alert vs silence accuracy | 0.919 | 0.814 | 0.938 |
| 3-way action accuracy | 0.895 | 0.69 | 0.929 |
| Real/fake accuracy | 0.948 | n/a | 0.971 |
| Offer level accuracy | 0.743 | n/a | 0.948 |
| Latency median / p95 (ms) | 743.55 / 889.66 | ~0 | 584.0 / 668.0 |
| API cost (USD) | 0 (local) | 0 | 0.124 |

Decider answers decisively on 83% of offers and is right 91% of the time on those; the rest get a warning.

Decider's own answer to "does it fit this user?" was right 41% of the time, so that comparison (price vs cap, level vs minimum) is done in code.

Failures: Decider 0, LLM 6.

## Alert accuracy by scenario

| Scenario | n | Decider | Rule | LLM |
|---|---|---|---|---|
| inflated_spike | 30 | 1.0 | 0.933 | 1.0 |
| genuine_drop | 30 | 0.833 | 0.567 | 0.933 |
| normal_fluctuation | 30 | 1.0 | 1.0 | 0.933 |
| recurring_sale | 30 | 0.967 | 0.967 | 0.9 |
| short_history | 30 | 1.0 | 0.867 | 1.0 |
| edge_10 | 30 | 0.667 | 0.6 | 0.833 |
| edge_25 | 30 | 0.967 | 0.767 | 0.967 |

## Calibration (expected calibration error, lower is better)

- is_real: 0.17
- level: 0.353
- level_prob: 0.231
