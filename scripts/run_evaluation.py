"""Run the evaluation against a live Decider server and Bedrock.

Usage:
  AWS_PROFILE=<profile> python scripts/run_evaluation.py --n 30 --lang en   # or --lang es
  python scripts/run_evaluation.py --n 30 --real-db dealjudge.db   # also compare with Knasta on real prices

Needs a running Decider server (see README) and Bedrock access for the LLM baseline.
"""

import argparse
import json
import urllib.request

from dealjudge import i18n
from dealjudge.baselines import LlmJudge
from dealjudge.client import DeciderClient
from dealjudge.evaluate import run_evaluation
from dealjudge.judge import Judge
from dealjudge.real_series import describe_real


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="cases per scenario, per split")
    ap.add_argument("--dev-seed", type=int, default=101)
    ap.add_argument("--test-seed", type=int, default=303)  # 101/202 were used while tuning the wording
    ap.add_argument("--lang", choices=i18n.LANGS, default=i18n.DEFAULT_LANG)
    ap.add_argument("--out", help="output folder (default: results/<lang>)")
    ap.add_argument("--real-db", help="SQLite from the price registrar, for the Knasta comparison")
    args = ap.parse_args()

    client = DeciderClient()
    with urllib.request.urlopen(f"{client.url}/health", timeout=10) as r:
        health = json.load(r)
    print(f"Decider: {health['checkpoint']} on {health['device']}")
    out = args.out or f"results/{args.lang}"
    judge = Judge(client, lang=args.lang)

    report = run_evaluation(
        args.dev_seed, args.test_seed, args.n, judge, LlmJudge(lang=args.lang), out,
        extra_meta={"decider_checkpoint": health["checkpoint"], "decider_device": health["device"]},
    )
    print(json.dumps({k: report[k] for k in ("meta", "alert_accuracy", "action_accuracy", "latency_ms", "cost", "failures")}, indent=2))

    if args.real_db:
        real = describe_real(args.real_db, judge)
        with open(f"{out}/real.json", "w") as f:
            json.dump(real, f, indent=2, ensure_ascii=False)
        print(f"real: {real['n']} products, Decider actions {real['decider_actions']}")


if __name__ == "__main__":
    main()
