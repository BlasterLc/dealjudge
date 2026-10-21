"""Live check against a running Decider server: prints the raw answers and the latency.

Usage: python scripts/smoke_decider.py [--lang en|es]
"""

import argparse
import json
import time
from datetime import date, timedelta

from dealjudge import i18n
from dealjudge.client import DeciderClient
from dealjudge.history import PricePoint, UserProfile, compute_stats, render_state
from dealjudge.questions import decider_questions

END = date(2026, 10, 20)


def series(prices):
    n = len(prices)
    return [PricePoint(END - timedelta(days=n - 1 - i), p) for i, p in enumerate(prices)]


CASES = {
    "a real 20% discount": ([40000] * 85 + [32000], None),
    "an inflated spike and back to the usual price": ([29990] * 60 + [39990] * 12 + [29990], 39990),
}

ap = argparse.ArgumentParser()
ap.add_argument("--lang", choices=i18n.LANGS, default=i18n.DEFAULT_LANG)
lang = ap.parse_args().lang
client = DeciderClient()
for name, (prices, advertised) in CASES.items():
    state = render_state(i18n.product_name(lang, "Wireless headphones"), compute_stats(series(prices)), advertised,
                         UserProfile(max_price=35000), lang)
    t0 = time.perf_counter()
    result = client.ask(state, decider_questions(lang))
    wall = (time.perf_counter() - t0) * 1000
    print(f"== {name}  (wall {wall:.0f} ms, server {result.latency_ms} ms)")
    print(json.dumps(result.answers, indent=2, ensure_ascii=False))
