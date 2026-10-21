"""End to end: a Strands agent (Bedrock) announces four simulated offers; the handler judges each.

Usage: AWS_PROFILE=<profile> python scripts/run_agent_demo.py [--lang en|es] [--threshold 0.1]
The threshold defaults to the one calibrated in results/<lang>/evaluation.json, if that file exists.
"""

import argparse
import json
import os

from dealjudge import i18n
from dealjudge.agent import build_agent
from dealjudge.client import DeciderClient
from dealjudge.generator import generate_cases
from dealjudge.handler import AlertLedger, DealjudgeHandler, VerdictLog
from dealjudge.judge import Judge
from dealjudge.policy import DEFAULT_THRESHOLD

SCENARIOS = ("inflated_spike", "genuine_drop", "normal_fluctuation", "short_history")


def calibrated_threshold(lang: str) -> float:
    try:
        path = f"results/{lang}/evaluation.json"
        with open(path) as f:
            return float(json.load(f)["meta"]["threshold"])
    except (OSError, KeyError, ValueError):
        return DEFAULT_THRESHOLD


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=i18n.LANGS, default=i18n.DEFAULT_LANG)
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    lang = args.lang
    threshold = args.threshold if args.threshold is not None else calibrated_threshold(lang)

    cases = {c.scenario: c for c in generate_cases(1, args.seed) if c.scenario in SCENARIOS}
    offers = {c.id: (c.series, c.advertised_list_price) for c in cases.values()}
    profile = next(iter(cases.values())).profile
    log, outbox = VerdictLog(), []
    judge = Judge(DeciderClient(), threshold=threshold, lang=lang)
    handler = DealjudgeHandler(judge, lambda oid: offers[oid], profile, log, AlertLedger())
    agent = build_agent(handler, log, outbox, lang=lang)

    ask, product_label, price_label = {
        "en": ("Announce these offers, one by one:", "product", "current price"),
        "es": ("Anuncia estas ofertas, una por una:", "producto", "precio actual"),
    }[lang]
    lines = [
        f"- offer_id={c.id}, {product_label}={i18n.product_name(lang, c.product)}, {price_label}={c.series[-1].price}"
        for c in cases.values()
    ]
    agent(ask + "\n" + "\n".join(lines))
    print("\n== Alerts sent ==")
    for o in outbox:
        print(f"[{o['action']}] {o['offer_id']}: {o['notice']}")
    print("\n== Simulated truth ==")
    for c in cases.values():
        print(f"{c.id}: should be {c.truth.action}")


if __name__ == "__main__":
    main()
