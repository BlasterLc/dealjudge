# Dealjudge: a 2B model that tells you when a discount is fake

*Tags: #strands-decider-2b #policy*

Every Cyber sale, the same trick: a price goes up a few weeks before the event, then "drops" to where it
always was, with a big red percentage next to it. I wanted an agent that watches the products I care about and
only bothers me when the discount is **real**, or tells me plainly when it is not sure.

[Video: link here] · [Repo: link here]

## The decision I handed to Decider 2B

For each offer, code computes the price history (median of the 90 days before any recent spike, minimum,
days since the last drop, whether there was a spike) and hands Strands Decider 2B a short text with one
figure per line. Decider answers typed questions about it: *is the real discount 10 % or more?* (yes/no) and
*what level of offer is it?* (`sin_oferta`, `marginal`, `buena`, `muy_buena`, `excepcional`).

Then **plain Python decides** (`policy.py`): a confident real discount that fits the user is announced; a
confident "not real" stays silent; **anything uncertain is announced with a visible warning**. A Strands
`InterventionHandler` applies that before the `enviar_aviso` tool runs, and Amazon Bedrock writes the alert text
from figures the code provides. The model is never the gate.

## What I measured

All numbers below are on **simulated** offers: 7 scenarios, 30 cases each, 210 test cases (seed 303). The
confidence threshold (0.1) was fixed on a separate dev split (seed 101), never on the test cases.

| Metric (test split) | Decider + rule | Old `cyber-watch` rule | Bedrock LLM (Claude Haiku 4.5) |
|---|---|---|---|
| Alert vs silence accuracy | 0.900 | 0.752 | 0.952 |
| 3-way action accuracy | 0.886 | 0.629 | 0.952 |
| Real vs fake accuracy | 0.943 | n/a | 0.981 |
| Offer level accuracy | 0.748 | n/a | 0.948 |
| Latency, median / p95 | 523 / 635 ms (local GPU) | ~0 | 568 / 647 ms |
| Failed calls | 0 | 0 | 4 |
| API cost | 0 (runs locally) | 0 | about US$0.13 for the run |

What this says, without spin:

- **Decider beats the old rule by 15 points** (0.900 vs 0.752) and is clearly better where the rule is blind:
  genuine drops that have already lasted a few days (0.77 vs 0.33, because the rule only compares today with
  yesterday), short histories and offers near the 25 % line.
- **A larger LLM is more accurate.** Haiku 4.5 scores 0.952 and wins on level accuracy (0.948 vs 0.748). Decider
  is weakest on the middle levels (`buena` 55 %, `muy_buena` 52 %) and ties the old rule on offers sitting right
  on the 10 % line (0.57).
- **What Decider adds is not raw accuracy.** It returns probabilities in one local call, with no API cost and no
  failed calls, and the code can use them: Decider answered decisively on 84 % of offers and was right 89 % of
  the time on those; the rest were announced with a warning instead of a guess. Calibration is imperfect (ECE
  0.17 for real/fake, 0.37 for level), which is why the threshold is fit on data.

The offers are **simulated**: a public generator builds 90-day series and the correct answer comes from the
series' own figures. That makes the benchmark about how well a 2B model reads figures, not about real stores.
The old `cyber-watch` rule (alert on a 20 % drop from the last price) is an independent baseline.

## Four things that surprised me

1. **Phrasing moved accuracy from 53 % to 94 %.** "Is this discount real?" was nearly a coin flip. "Look at the
   line *real discount vs median*: is it 10 % or more?" worked. Point the model at the figure.
2. **Decider answered worse than chance on a two-part comparison.** "Does this fit the user?" (price against a
   cap *and* a level against a minimum) scored 37-41 % in development and 43 % on the test split. I moved that comparison into code, kept the model's
   answer, and reported it. It matches the model card's own warning about harder tasks.
3. **`confidence` is not a probability.** For the offer level it sat on a low scale (a correct pick at P=0.30
   reported 0.13), so a fixed 0.70 threshold made everything warn. I fit the threshold on a dev split with a rule
   that only gives a decisive answer when it is right more than half the time.
4. **Hardware matters more than it looks.** About 270 ms per call (three questions) on a laptop GPU; about 12 s on
   CPU. When I unplugged the charger, the GPU vanished from WSL and the server silently fell back to CPU.

## The reusable pattern: `#policy`

`patterns/policy/policy_gate.py` is one file: you give it typed questions, a function that renders the situation
as text, and your own `decide(answers)`; it maps the result to `Proceed`, `Deny` or `Guide`, and fails closed if
the server does not answer. Wiring and lessons are in its README.

## Limits

Simulated benchmark; real prices have no ground truth (Knasta's own state is stored only as a reference);
histories under 14 days always warn by rule; scraping retail sites is a grey zone; email delivery, adding
products by message and Decider on SageMaker are not built.

## Try it

`uv venv && uv pip install -e ".[dev]"`, start `strands-decider serve`, then `scripts/run_evaluation.py` and
`python -m http.server -d web`. Everything is Apache-2.0.
