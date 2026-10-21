"""Judge six simulated offers with the live Decider and Bedrock, and write the page's data.

Usage: AWS_PROFILE=<profile> python scripts/build_demo.py [--lang en|es] [--seed 7]
Writes web/data/demo.<lang>.json. The threshold is the one calibrated in results/<lang>/evaluation.json.
"""

import argparse

from dealjudge import i18n
from dealjudge.demo import build_demo

ap = argparse.ArgumentParser()
ap.add_argument("--lang", choices=i18n.LANGS, default=i18n.DEFAULT_LANG)
ap.add_argument("--seed", type=int, default=7)
args = ap.parse_args()
build_demo(args.seed, f"web/data/demo.{args.lang}.json", lang=args.lang)
print(f"wrote web/data/demo.{args.lang}.json")
