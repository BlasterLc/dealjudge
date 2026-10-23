# Video script, English narration (under 3:00)

Spanish version: [video-script.es.md](video-script.es.md). Record one language per video; use the matching
`--lang`/page language and the numbers from `results/<lang>/evaluation.json`. This script uses `results/en/`.

Narration in English, Spanish subtitles (or the reverse with the Spanish script). Use only the fictional stores shown
in the page. No music, or music with a license that allows it. Screen: the Dealjudge page at 1280 px, in the same
language as the narration. Record the pages in `web/` from a local server. Do not show third-party brand names
(the related-work section of the article is not filmed).

| Time | Screen | Narration |
|---|---|---|
| 0:00-0:20 | A price tag with a big red "-25 %"; cut to the page | "Every Cyber sale has discounts that are not: the price goes up weeks before and then drops back to where it always was. Dealjudge judges every offer against 90 days of prices." |
| 0:20-0:55 | Open the inflated-spike product: the verdict "stay silent", then the "How Decider decided" panel (three answers, confidence against the threshold). Open the chart fold and zoom the red spike | "Here the store advertises a big discount, but the price was inflated: the 90-day median is almost the same as today. Decider reads the figures and answers with confidence: it is not real. Dealjudge stays quiet, and explains why." |
| 0:55-1:25 | Open the genuine-drop product (alert), show the alert text | "This one is a real drop, far below the median. Only here does it alert, with the figures behind it; Bedrock writes the text." |
| 1:25-1:50 | Open the short-history product (alert with warning) | "When it is not sure, or there is little history, it still alerts but with a visible warning. Doubt is never hidden." |
| 1:50-2:30 | `results/en/evaluation.md`: the table and the calibration lines | "We measured it against the old rule and against a large LLM, on simulated offers, declared as such. Decider gets 94 % right on whether to alert, against 81 % for the old rule. The Bedrock LLM scores the same, a tie, and beats it at grading how good the offer is. What Decider adds is one local call of about 280 milliseconds with no API cost and no failed calls, and probabilities the code uses to warn when it doubts." |
| 2:30-2:45 | The figure `docs/img/how-it-works.en.png` (typed questions, code rule), then `patterns/policy/policy_gate.py` and its README | "The pattern is reusable: typed questions, your own function decides, fails closed. One file." |
| 2:45-2:55 | Repo URL and article title | "Dealjudge, Apache-2.0. Code and article at the link." |

Check before publishing: public link, under 3:00, no third-party brands visible, no copyrighted music, subtitles on,
every figure matches `results/en/evaluation.json` (0.943, 0.814, 0.938), and the page shown is the final one.
