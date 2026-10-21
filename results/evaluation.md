# Evaluation (simulated data)

All figures are on **simulated** offers (210 test cases, seed 303); the confidence threshold (0.1) was fixed on a separate dev split (seed 101). Truth is computed from each price series by `truth_for()`; see `dealjudge/generator.py`.

| Metric | Decider + rule | cyber-watch rule | LLM |
|---|---|---|---|
| Alert vs silence accuracy | 0.9 | 0.752 | 0.952 |
| 3-way action accuracy | 0.886 | 0.629 | 0.952 |
| Real/fake accuracy | 0.943 | n/a | 0.981 |
| Offer level accuracy | 0.748 | n/a | 0.948 |
| Latency median / p95 (ms) | 522.52 / 635.46 | ~0 | 568.0 / 647.0 |
| API cost (USD) | 0 (local) | 0 | 0.1253 |

Decider answers decisively on 84% of offers and is right 89% of the time on those; the rest get a warning.

Decider's own answer to "does it fit this user?" was right 43% of the time, so that comparison (price vs cap, level vs minimum) is done in code.

Failures: Decider 0, LLM 4.

## Alert accuracy by scenario

| Scenario | n | Decider | Rule | LLM |
|---|---|---|---|---|
| pico_inflado | 30 | 1.0 | 0.9 | 1.0 |
| baja_genuina | 30 | 0.767 | 0.333 | 1.0 |
| fluctuacion_normal | 30 | 1.0 | 1.0 | 1.0 |
| oferta_recurrente | 30 | 1.0 | 0.9 | 0.9 |
| historial_corto | 30 | 1.0 | 0.867 | 1.0 |
| limite_10 | 30 | 0.567 | 0.567 | 0.9 |
| limite_25 | 30 | 0.967 | 0.7 | 0.867 |

## Calibration (expected calibration error, lower is better)

- is_real: 0.17
- level: 0.37
- level_prob: 0.236
