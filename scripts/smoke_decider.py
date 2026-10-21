"""Live check against a running Decider server: prints the raw answers and the latency.

Usage: python scripts/smoke_decider.py
"""

import json
import time
from datetime import date, timedelta

from dealjudge.client import DeciderClient
from dealjudge.history import PricePoint, UserProfile, compute_stats, render_state
from dealjudge.questions import decider_questions

END = date(2026, 10, 20)


def series(prices):
    n = len(prices)
    return [PricePoint(END - timedelta(days=n - 1 - i), p) for i, p in enumerate(prices)]


CASES = {
    "descuento real de 20 %": ([40000] * 85 + [32000], None),
    "pico inflado y vuelta al precio de siempre": ([29990] * 60 + [39990] * 12 + [29990], 39990),
}

client = DeciderClient()
for name, (prices, advertised) in CASES.items():
    state = render_state("Audifonos Aura X2", compute_stats(series(prices)), advertised, UserProfile(max_price=35000))
    t0 = time.perf_counter()
    result = client.ask(state, decider_questions())
    wall = (time.perf_counter() - t0) * 1000
    print(f"== {name}  (reloj {wall:.0f} ms, servidor {result.latency_ms} ms)")
    print(json.dumps(result.answers, indent=2, ensure_ascii=False))
