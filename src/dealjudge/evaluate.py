"""Evaluation: Decider vs the old rule vs an LLM, on the same simulated offers.

A development split (``dev_seed``) fixes the confidence threshold; a test split
(``test_seed``) is what gets reported. Everything here is on simulated data and the report
says so.
"""

import json
import math
import os
from statistics import median

from dealjudge.baselines import LlmJudgement, cyber_watch_rule
from dealjudge.generator import SCENARIOS, Case, Truth, generate_cases
from dealjudge.history import compute_stats, render_state
from dealjudge.judge import Judgement
from dealjudge.levels import LEVELS
from dealjudge.policy import GOOD_LEVELS, MIN_HISTORY_DAYS, decide

# USD per million tokens for the LLM baseline (Claude Haiku 4.5 on Bedrock).
# Verify against the Bedrock pricing page before publishing.
LLM_PRICE_USD_PER_MTOK = {"input": 1.0, "output": 5.0}
CANDIDATE_THRESHOLDS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


def accuracy(pred, truth) -> float:
    return sum(p == t for p, t in zip(pred, truth)) / len(truth) if len(truth) else 0.0


def calibration_bins(confidences, correct, n_bins: int = 5) -> list[dict]:
    bins = [{"lo": i / n_bins, "hi": (i + 1) / n_bins, "n": 0, "_conf": 0.0, "_hits": 0} for i in range(n_bins)]
    for c, ok in zip(confidences, correct):
        b = bins[min(int(c * n_bins), n_bins - 1)]
        b["n"] += 1
        b["_conf"] += c
        b["_hits"] += bool(ok)
    return [
        {
            "lo": b["lo"],
            "hi": b["hi"],
            "n": b["n"],
            "mean_confidence": round(b["_conf"] / b["n"], 3) if b["n"] else None,
            "accuracy": b["_hits"] / b["n"] if b["n"] else None,
        }
        for b in bins
    ]


def expected_calibration_error(confidences, correct, n_bins: int = 5) -> float:
    total = len(confidences)
    if not total:
        return 0.0
    return sum(
        b["n"] / total * abs(b["accuracy"] - b["mean_confidence"])
        for b in calibration_bins(confidences, correct, n_bins)
        if b["n"]
    )


def summarize_latency(values) -> dict:
    if not values:
        return {"median": None, "p95": None}
    ordered = sorted(values)
    return {"median": median(ordered), "p95": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]}


def llm_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * LLM_PRICE_USD_PER_MTOK["input"] + output_tokens * LLM_PRICE_USD_PER_MTOK["output"]) / 1e6


def llm_action(j: LlmJudgement, history_days: int) -> str:
    """The LLM answers the same three questions; the same deterministic rule turns them into an action."""
    if j.failed or history_days < MIN_HISTORY_DAYS:
        return "avisar_con_advertencia"
    return "avisar" if j.is_real and j.fits_user and j.level in GOOD_LEVELS else "callar"


def calibrate_threshold(dev, candidates=CANDIDATE_THRESHOLDS) -> float:
    """The threshold with the best action accuracy on ``dev`` = [(Judgement, Truth, history_days)].
    Ties go to the higher (more cautious) threshold."""
    def score(threshold):
        return sum(
            decide(j.is_real_p, j.level, j.level_conf, j.fits_p, days, threshold).action == t.action
            for j, t, days in dev
        )

    return max(sorted(candidates), key=lambda c: (score(c), c))


def _inputs(case: Case):
    stats = compute_stats(case.series)
    return stats, render_state(case.product, stats, case.advertised_list_price, case.profile)


def _rule_action(case: Case) -> str:
    prev = case.series[-2].price if len(case.series) > 1 else 0
    return cyber_watch_rule(prev, case.series[-1].price)


def _alerts(actions) -> list[bool]:
    return [a != "callar" for a in actions]


def run_evaluation(dev_seed, test_seed, n_per_scenario, judge, llm, out_dir, extra_meta=None) -> dict:
    # 1. fix the threshold on the development split
    dev = []
    for case in generate_cases(n_per_scenario, dev_seed):
        stats, state = _inputs(case)
        dev.append((judge.judge(state, stats.days_of_history), case.truth, stats.days_of_history))
    threshold = calibrate_threshold(dev)

    # 2. judge the test split with all three competitors
    cases = generate_cases(n_per_scenario, test_seed)
    rows = []
    for case in cases:
        stats, state = _inputs(case)
        days = stats.days_of_history
        j = judge.judge(state, days)
        decision = decide(j.is_real_p, j.level, j.level_conf, j.fits_p, days, threshold)
        lj = llm.judge(state)
        rows.append({"case": case, "days": days, "j": j, "decider": decision.action,
                     "rule": _rule_action(case), "lj": lj, "llm": llm_action(lj, days)})

    truth_actions = [r["case"].truth.action for r in rows]
    truth_alerts = _alerts(truth_actions)
    pred = {k: [r[k] for r in rows] for k in ("decider", "rule", "llm")}
    ok_d = [not r["j"].failed for r in rows]
    ok_l = [not r["lj"].failed for r in rows]

    is_real = {
        "decider": accuracy([(r["j"].is_real_p >= 0.5) if o else None for r, o in zip(rows, ok_d)],
                            [r["case"].truth.is_real for r in rows]),
        "llm": accuracy([r["lj"].is_real if o else None for r, o in zip(rows, ok_l)],
                        [r["case"].truth.is_real for r in rows]),
    }
    level = {
        "decider": accuracy([r["j"].level for r in rows], [r["case"].truth.level for r in rows]),
        "llm": accuracy([r["lj"].level for r in rows], [r["case"].truth.level for r in rows]),
    }
    by_scenario = {}
    for s in SCENARIOS:
        sel = [r for r in rows if r["case"].scenario == s]
        t = [r["case"].truth.action for r in sel]
        by_scenario[s] = {"n": len(sel)} | {
            k: round(accuracy(_alerts([r[k] for r in sel]), _alerts(t)), 3) for k in ("decider", "rule", "llm")
        }
    by_level = {}
    for lv in LEVELS:
        sel = [r for r in rows if r["case"].truth.level == lv]
        by_level[lv] = {"n": len(sel)} | {
            "decider": round(accuracy([r["j"].level for r in sel], [lv] * len(sel)), 3),
            "llm": round(accuracy([r["lj"].level for r in sel], [lv] * len(sel)), 3),
        }

    good = [r for r, o in zip(rows, ok_d) if o]
    conf_real = [max(r["j"].is_real_p, 1 - r["j"].is_real_p) for r in good]
    hit_real = [(r["j"].is_real_p >= 0.5) == r["case"].truth.is_real for r in good]
    conf_level = [r["j"].level_conf for r in good]
    hit_level = [r["j"].level == r["case"].truth.level for r in good]
    conf_prob = [r["j"].level_prob for r in good]
    calibration = {
        name: {"ece": round(expected_calibration_error(c, h), 3), "bins": calibration_bins(c, h)}
        for name, c, h in (("is_real", conf_real, hit_real), ("level", conf_level, hit_level),
                           ("level_prob", conf_prob, hit_level))
    }

    report = {
        "meta": {
            "simulated": True, "n_per_scenario": n_per_scenario, "dev_seed": dev_seed, "test_seed": test_seed,
            "n_dev": len(dev), "n_test": len(rows), "threshold": threshold,
            "llm_model": getattr(llm, "model_id", "unknown"),
            "note": "Simulated offers generated by dealjudge.generator; truth comes from truth_for().",
        } | (extra_meta or {}),
        "alert_accuracy": {k: round(accuracy(_alerts(v), truth_alerts), 3) for k, v in pred.items()},
        "action_accuracy": {k: round(accuracy(v, truth_actions), 3) for k, v in pred.items()},
        "is_real_accuracy": {k: round(v, 3) for k, v in is_real.items()},
        "level_accuracy": {k: round(v, 3) for k, v in level.items()},
        "by_scenario": by_scenario,
        "by_level": by_level,
        "latency_ms": {
            "decider": summarize_latency([r["j"].latency_ms for r in rows if r["j"].latency_ms is not None]),
            "llm": summarize_latency([r["lj"].latency_ms for r in rows if not r["lj"].failed]),
        },
        "cost": {
            "decider_api_usd": 0.0,
            "llm_usd": round(llm_cost_usd(sum(r["lj"].input_tokens for r in rows),
                                          sum(r["lj"].output_tokens for r in rows)), 4),
        },
        "calibration": calibration,
        "failures": {"decider": sum(r["j"].failed for r in rows), "llm": sum(r["lj"].failed for r in rows)},
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "evaluation.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=lambda x: None if isinstance(x, float) and math.isnan(x) else x)
    with open(os.path.join(out_dir, "evaluation.md"), "w") as f:
        f.write(render_markdown(report))
    return report


def render_markdown(report: dict) -> str:
    m, a = report["meta"], report["alert_accuracy"]
    lines = [
        "# Evaluation (simulated data)",
        "",
        f"All figures are on **simulated** offers ({m['n_test']} test cases, seed {m['test_seed']}); "
        f"the confidence threshold ({m['threshold']}) was fixed on a separate dev split (seed {m['dev_seed']}). "
        "Truth is computed from each price series by `truth_for()`; see `dealjudge/generator.py`.",
        "",
        "| Metric | Decider + rule | cyber-watch rule | LLM |",
        "|---|---|---|---|",
        f"| Alert vs silence accuracy | {a['decider']} | {a['rule']} | {a['llm']} |",
        f"| 3-way action accuracy | {report['action_accuracy']['decider']} | {report['action_accuracy']['rule']} | {report['action_accuracy']['llm']} |",
        f"| Real/fake accuracy | {report['is_real_accuracy']['decider']} | n/a | {report['is_real_accuracy']['llm']} |",
        f"| Offer level accuracy | {report['level_accuracy']['decider']} | n/a | {report['level_accuracy']['llm']} |",
        f"| Latency median / p95 (ms) | {report['latency_ms']['decider']['median']} / {report['latency_ms']['decider']['p95']} | ~0 | {report['latency_ms']['llm']['median']} / {report['latency_ms']['llm']['p95']} |",
        f"| API cost (USD) | 0 (local) | 0 | {report['cost']['llm_usd']} |",
        "",
        f"Failures: Decider {report['failures']['decider']}, LLM {report['failures']['llm']}.",
        "",
        "## Alert accuracy by scenario",
        "",
        "| Scenario | n | Decider | Rule | LLM |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| {s} | {v['n']} | {v['decider']} | {v['rule']} | {v['llm']} |" for s, v in report["by_scenario"].items()]
    lines += ["", "## Calibration (expected calibration error, lower is better)", ""]
    lines += [f"- {name}: {v['ece']}" for name, v in report["calibration"].items()]
    return "\n".join(lines) + "\n"
