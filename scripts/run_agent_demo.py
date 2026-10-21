"""End to end: a Strands agent (Bedrock) announces four simulated offers; the handler judges each.

Usage: AWS_PROFILE=<profile> python scripts/run_agent_demo.py [--threshold 0.1]
The threshold defaults to the one calibrated in results/evaluation.json, if that file exists.
"""

import argparse
import json
import os

from dealjudge.agent import build_agent
from dealjudge.client import DeciderClient
from dealjudge.generator import generate_cases
from dealjudge.handler import AlertLedger, DealjudgeHandler, VerdictLog
from dealjudge.judge import Judge
from dealjudge.policy import DEFAULT_THRESHOLD

SCENARIOS = ("inflated_spike", "genuine_drop", "normal_fluctuation", "short_history")


def calibrated_threshold(path: str = "results/evaluation.json") -> float:
    try:
        with open(path) as f:
            return float(json.load(f)["meta"]["threshold"])
    except (OSError, KeyError, ValueError):
        return DEFAULT_THRESHOLD


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=calibrated_threshold())
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    cases = {c.scenario: c for c in generate_cases(1, args.seed) if c.scenario in SCENARIOS}
    offers = {c.id: (c.series, c.advertised_list_price) for c in cases.values()}
    profile = next(iter(cases.values())).profile
    log, outbox = VerdictLog(), []
    handler = DealjudgeHandler(Judge(DeciderClient(), threshold=args.threshold), lambda oid: offers[oid], profile, log, AlertLedger())
    agent = build_agent(handler, log, outbox)

    lines = [f"- offer_id={c.id}, producto={c.product}, precio actual={c.series[-1].price}" for c in cases.values()]
    agent("Anuncia estas ofertas, una por una:\n" + "\n".join(lines))
    print("\n== Avisos enviados ==")
    for o in outbox:
        print(f"[{o['action']}] {o['offer_id']}: {o['notice']}")
    print("\n== Verdad simulada ==")
    for c in cases.values():
        print(f"{c.id}: debía ser {c.truth.action}")


if __name__ == "__main__":
    main()
