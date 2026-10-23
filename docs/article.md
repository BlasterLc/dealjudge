# Dealjudge: a 2B model that tells you when a discount is fake

*Tags: #strands-decider-2b #policy*

*Spanish version: [article.es.md](article.es.md)*

Every Cyber sale, the same trick: a price goes up a few weeks before the event, then "drops" to where it
always was, with a big red percentage next to it. I wanted an agent that watches the products I care about and
only bothers me when the discount is **real**, or tells me plainly when it is not sure.

[Video: link here] · [Repo: link here]

## The decision I handed to Decider 2B

For each offer, code computes the price history (median of the 90 days before any recent spike, minimum,
days since the last drop, whether there was a spike) and hands Strands Decider 2B a short text with one
figure per line. Decider answers typed questions about it: *is the real discount 10 % or more?* (yes/no) and
*what level of offer is it?* (`no_deal`, `marginal`, `good`, `very_good`, `exceptional`).

Then **plain Python decides** (`policy.py`): a confident real discount that fits the user is announced
(`alert`); a confident "not real" stays silent (`stay_silent`); **anything uncertain is announced with a visible
warning** (`alert_with_warning`). A Strands `InterventionHandler` applies that before the `send_alert` tool runs,
and Amazon Bedrock writes the alert text from figures the code provides. The model is never the gate.

![How Dealjudge decides: code computes the history, Decider answers three typed questions, a plain-Python confidence rule picks alert, alert with warning or stay silent, and Bedrock only words the alert](docs/img/how-it-works.en.png)

Everything the model reads and the user sees exists in English and Spanish, one language per run.

## What I measured

All numbers below are on **simulated** offers: 7 scenarios, 30 cases each, 210 test cases (seed 303), run once in
English and once in Spanish. The confidence threshold (0.1) was fixed on a separate dev split (seed 101), never on
the test cases.

| Metric (test split) | Decider + rule, EN | Decider + rule, ES | Old `cyber-watch` rule | Claude Haiku 4.5, EN / ES |
|---|---|---|---|---|
| Alert vs silence accuracy | 0.943 | 0.919 | 0.814 | 0.938 / 0.938 |
| 3-way action accuracy | 0.943 | 0.895 | 0.690 | 0.933 / 0.929 |
| Real vs fake accuracy | 1.000 | 0.948 | n/a | 0.962 / 0.971 |
| Offer level accuracy | 0.790 | 0.743 | n/a | 0.919 / 0.948 |
| Failed calls | 0 | 0 | 0 | 8 / 6 |
| API cost | 0 (local) | 0 (local) | 0 | US$0.11 / US$0.12 for the run |

What this says, without spin:

- **Decider beats the old rule by 13 points in English and 10 in Spanish** (0.943 and 0.919 vs 0.814). It is
  clearly better where the rule is blind: genuine drops that have already lasted a few days (1.00 vs 0.57 in
  English, because the rule only compares today with yesterday) and offers near the 25 % line (1.00 vs 0.77).
- **Against a larger LLM it is a tie on the decision that matters, and a loss on the level.** Haiku 4.5 scores
  0.938 on alert vs silence, the same as Decider within noise (n=210), and wins on level accuracy (0.92-0.95 vs
  0.74-0.79). Decider is weakest on the middle levels (`good` 0.70, `very_good` 0.52 in English) and on offers
  sitting right on the 10 % line, where it only matches the old rule (0.60 English, 0.67 Spanish; the LLM scores 0.83).
- **What Decider adds is not raw accuracy.** It returns probabilities in one local call, with no API cost and no
  failed calls (the LLM failed 8 and 6 times, which I count as warnings), and the code can use them: Decider
  answered decisively on 86 % of offers in English (83 % in Spanish) and was right 93 % (91 %) of the time on
  those; the rest were announced with a warning instead of a guess.
- **Calibration is imperfect.** For real/fake the expected calibration error is 0.13 (EN) and 0.17 (ES), mostly
  because the model is under-confident (right 100 % of the time at a mean confidence of about 0.87 in English). For the
  offer level it is 0.37 and 0.35, which is why the threshold is fit on data.
- **Latency: same order as the LLM, not faster.** The evaluation runs measured a median of 484 ms (EN) and 744 ms
  (ES) for Decider and 574 / 584 ms for Haiku. The two Decider figures differ for the same model, so I do not claim
  a speed advantage. Measured alone, the same three-question call took about 300 ms in both languages (30 calls
  each, laptop RTX 4050).

The offers are **simulated**: a public generator builds 90-day series and the correct answer comes from the
series' own figures. That makes the benchmark about how well a 2B model reads figures, not about real stores.
The old `cyber-watch` rule (alert on a 20 % drop from the last price) is an independent baseline. I also record
real prices from three Chilean retail sites every six hours, but they have no ground truth, so they are not part
of the benchmark.

## Five things that surprised me

1. **Phrasing moved accuracy from 53 % to 94 %.** On the development split, "Is this discount real?" was nearly
   a coin flip. "Look at the line *real discount vs median*: is it 10 % or more?" worked. Point the model at the figure.
2. **Decider answered worse than chance on a two-part comparison.** "Does this fit the user?" (price against a
   cap *and* a level against a minimum) scored 37-41 % in development and 44 % (EN) / 41 % (ES) on the test split.
   I moved that comparison into code, kept the model's answer, and reported it. It matches the model card's own
   warning about harder tasks.
3. **`confidence` is not a probability.** For the offer level it sat on a low scale (a correct pick at P=0.30
   reported 0.13), so a fixed 0.70 threshold made everything warn. I fit the threshold on a dev split with a rule
   that only gives a decisive answer when it is right more than half the time.
4. **It reads English better than Spanish.** Same offers, same questions translated: real/fake 1.00 vs 0.95,
   level 0.79 vs 0.74, alert 0.943 vs 0.919. The gap showed up in the same direction on the development seed,
   and the Bedrock LLM did not have it. If your users write in another language, test the model in that language.
5. **Hardware matters more than it looks.** About 300 ms per call (three questions) on a laptop GPU; about 12 s on
   CPU. When I unplugged the charger, the GPU vanished from WSL and the server silently fell back to CPU.

## Related work

Price trackers such as Knasta, SoloTodo, Keepa and CamelCamelCamel chart the history and alert on a threshold;
they do not say whether a discount is real. Browser extensions (for example Fake Discount BG, SmartPrice Guard and
DealFury) flag inflated "before" prices with rules, and an Apify actor, Deal Quality Scorer, returns a score, an
`alertWorthy` flag and a `confidence` from the historical median, which is the closest to Dealjudge's output
shape. A security vendor's Black Friday advice is to paste the history into an LLM and ask; that is the baseline I
measure against. I found no published accuracy figures for any of these tools and I have not tested them: this
comes from their public listings. What Dealjudge adds is a measured comparison, a verdict that depends on the
user's own cap and minimum, a policy that warns instead of guessing, and the pattern published as one reusable file.

## The reusable pattern: `#policy`

`patterns/policy/policy_gate.py` is one file: you give it typed questions, a function that renders the situation
as text, and your own `decide(answers)`; it maps the result to `Proceed`, `Deny` or `Guide`, and fails closed if
the server does not answer. Wiring and lessons are in its README (English and Spanish).

## Limits

Simulated benchmark; real prices have no ground truth (Knasta's own state is stored only as a reference);
histories under 14 days always warn by rule; scraping retail sites is a grey zone; email delivery, adding
products by message and Decider on SageMaker are not built.

## Try it

`uv venv && uv pip install -e ".[dev]"`, start `strands-decider serve`, then
`scripts/run_evaluation.py --lang en` and `python -m http.server -d web`. Everything is Apache-2.0.
