"""Exports the demo data the web page reads: six simulated offers, each already judged.

Everything here is simulated: the series come from the generator and the stores are invented.
"""

import json
import os

from dealjudge.client import DeciderClient
from dealjudge.generator import generate_cases
from dealjudge.history import compute_stats, fits_profile, render_state
from dealjudge.judge import Judge
from dealjudge.notice import write_notice
from dealjudge.policy import DEFAULT_THRESHOLD

DEMO_SCENARIOS = ("pico_inflado", "pico_inflado", "baja_genuina", "baja_genuina", "historial_corto", "fluctuacion_normal")
STORES = ("Casa Aurora", "Electro Faro", "Mercado Sur", "Bazar Cobre", "Tienda Norte", "Almacén Luna")


def _threshold(path: str = "results/evaluation.json") -> float:
    try:
        with open(path) as f:
            return float(json.load(f)["meta"]["threshold"])
    except (OSError, KeyError, ValueError):
        return DEFAULT_THRESHOLD


def build_demo(seed: int, out_path: str, judge=None, bedrock_client=None) -> None:
    judge = judge or Judge(DeciderClient(), threshold=_threshold())
    pool: dict[str, list] = {}
    for case in generate_cases(len(STORES) + 2, seed):
        pool.setdefault(case.scenario, []).append(case)
    taken: dict[str, int] = {}
    cases = []
    for i, scenario in enumerate(DEMO_SCENARIOS):
        n = taken.get(scenario, 0)
        taken[scenario] = n + 1
        case = pool[scenario][(3 * i + n) % len(pool[scenario])]  # varied products across the six
        stats = compute_stats(case.series)
        state = render_state(case.product, stats, case.advertised_list_price, case.profile)
        j = judge.judge(state, stats.days_of_history, fits_profile(stats, case.profile))
        action = j.decision.action
        notice = (
            write_notice(j, stats, case.product, bedrock_client)
            if action != "callar"
            else f"No se avisó. {j.decision.reason}"
        )
        cases.append(
            {
                "id": case.id,
                "scenario": scenario,
                "product": case.product,
                "store_label": STORES[i],
                "series": [{"day": p.day.isoformat(), "price": p.price} for p in case.series],
                "baseline_median": stats.baseline_median,
                "current": stats.current,
                "advertised_list_price": case.advertised_list_price,
                "stats": {
                    "min_price": stats.min_price,
                    "days_of_history": stats.days_of_history,
                    "days_since_last_drop": stats.days_since_last_drop,
                    "spike_peak": stats.spike_peak,
                    "real_discount_pct": stats.real_discount_pct,
                },
                "verdict": {
                    "action": action,
                    "level": j.level,
                    "confidence": round(j.decision.confidence, 2),
                    "reason": j.decision.reason,
                },
                "notice": notice,
            }
        )
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"simulated": True, "seed": seed, "threshold": getattr(judge, "threshold", None), "cases": cases}, f, ensure_ascii=False, indent=2)
