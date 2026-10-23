"""How the confidence threshold trades coverage for accuracy, on the development split.

Usage: python scripts/threshold_sweep.py [--lang en|es] [--n 30] [--seed 101]

Judges the development cases once with the live Decider, then replays the confidence rule over a grid of
thresholds. A case is "decisive" when the rule commits to alert or stay_silent (the rest are announced with a
warning). The test split is never used here: this is the picture behind the threshold that
``calibrate_threshold`` fixes on the development split. Writes results/threshold/<lang>/sweep.{json,md,svg}.
"""

import argparse
import json
import os
from collections import Counter

from dealjudge import i18n
from dealjudge.client import DeciderClient
from dealjudge.evaluate import _utility, calibrate_threshold
from dealjudge.generator import generate_cases
from dealjudge.history import compute_stats, fits_profile, render_state
from dealjudge.judge import Judge
from dealjudge.policy import decide

GRID = [round(0.05 * i, 2) for i in range(1, 19)]  # 0.05 .. 0.90


def sweep(dev, grid=GRID):
    """dev = [(Judgement, Truth, history_days)]. One row per threshold."""
    rows = []
    for th in grid:
        actions = [decide(j.is_real_p, j.level, j.level_conf, j.effective_fits_p, days, th).action for j, _, days in dev]
        truths = [t.action for _, t, _ in dev]
        decisive = [(a, t) for a, t in zip(actions, truths) if a != "alert_with_warning"]
        rows.append({
            "threshold": th,
            "coverage": round(len(decisive) / len(dev), 3),
            "decisive_accuracy": round(sum(a == t for a, t in decisive) / len(decisive), 3) if decisive else None,
            "action_accuracy": round(sum(a == t for a, t in zip(actions, truths)) / len(dev), 3),
            "mean_utility": round(sum(_utility(a, t) for a, t in zip(actions, truths)) / len(dev), 3),
        })
    return rows


def chart_svg(rows, chosen, lang):
    T = {"en": ("Threshold on the confidence", "share of offers", "Decisive answers (coverage)", "Right when decisive", "Mean utility", "chosen on this split"),
         "es": ("Umbral de seguridad", "proporción de ofertas", "Respuestas decisivas (cobertura)", "Acierto cuando decide", "Utilidad media", "elegido en esta partición")}[lang]
    W, H, L, R, TOP, B = 920, 470, 70, 30, 40, 130
    x = lambda th: L + th / 0.9 * (W - L - R)  # noqa: E731
    y = lambda v: TOP + (1 - v) * (H - TOP - B)  # noqa: E731
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{T[1]}">',
         '<style>text{font-family:Inter,"Segoe UI",Helvetica,Arial,sans-serif;fill:#3f3f46;font-size:13px}.t{font-size:15px;font-weight:600;fill:#0a0a0a}</style>',
         f'<rect width="{W}" height="{H}" fill="#fff"/>']
    for v in (0, 0.25, 0.5, 0.75, 1):
        o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(v)}" y2="{y(v)}" stroke="#e4e4e7"/><text x="{L-10}" y="{y(v)+4}" text-anchor="end">{v:g}</text>')
    for th in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        o.append(f'<text x="{x(th)}" y="{H-B+20}" text-anchor="middle">{th:g}</text>')
    o.append(f'<text x="{(L+W-R)/2}" y="{H-B+44}" text-anchor="middle" class="t">{T[0]}</text>')
    o.append(f'<text x="18" y="{(TOP+H-B)/2}" transform="rotate(-90 18 {(TOP+H-B)/2})" text-anchor="middle">{T[1]}</text>')
    series = [("coverage", "#2563eb", "", T[2]), ("decisive_accuracy", "#0a0a0a", "", T[3]), ("mean_utility", "#92400e", "6 5", T[4])]
    for key, color, dash, _ in series:
        pts = " ".join(f"{x(r['threshold']):.1f},{y(r[key]):.1f}" for r in rows if r[key] is not None)
        o.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round" {"stroke-dasharray=" + chr(34) + dash + chr(34) if dash else ""}/>')
    o.append(f'<line x1="{x(chosen)}" x2="{x(chosen)}" y1="{TOP}" y2="{H-B}" stroke="#2563eb" stroke-width="1.5" stroke-dasharray="3 4"/>')
    o.append(f'<text x="{x(chosen)+8}" y="{y(0.62)}" style="fill:#1d4ed8;font-weight:600">{chosen:g}: {T[5]}</text>')
    for i, (_, color, dash, label) in enumerate(series):
        yy = H - B + 74 + i * 20
        o.append(f'<line x1="{L}" x2="{L+34}" y1="{yy-4}" y2="{yy-4}" stroke="{color}" stroke-width="2.4" {"stroke-dasharray=" + chr(34) + dash + chr(34) if dash else ""}/><text x="{L+44}" y="{yy}">{label}</text>')
    o.append("</svg>")
    return "\n".join(o)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=i18n.LANGS, default=i18n.DEFAULT_LANG)
    ap.add_argument("--n", type=int, default=30, help="cases per scenario")
    ap.add_argument("--seed", type=int, default=101, help="development seed (never the test seed)")
    args = ap.parse_args()

    judge = Judge(DeciderClient(), lang=args.lang)
    dev = []
    for case in generate_cases(args.n, args.seed):
        stats = compute_stats(case.series)
        state = render_state(i18n.product_name(args.lang, case.product), stats, case.advertised_list_price, case.profile, args.lang)
        dev.append((judge.judge(state, stats.days_of_history, fits_profile(stats, case.profile)), case.truth, stats.days_of_history))
    failed = sum(j.failed for j, _, _ in dev)
    chosen = calibrate_threshold(dev)
    rows = sweep(dev)
    # Why the rule warned at the chosen threshold: the history rule and the confidence gate are different things.
    reasons = Counter(decide(j.is_real_p, j.level, j.level_conf, j.effective_fits_p, days, chosen).reason
                      for j, _, days in dev)
    warn_reasons = {k: v for k, v in sorted(reasons.items()) if k in ("short_history", "low_confidence", "unreadable", "unknown_level")}

    out_dir = os.path.join("results", "threshold", args.lang)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sweep.json"), "w") as f:
        json.dump({"meta": {"lang": args.lang, "dev_seed": args.seed, "cases": len(dev), "decider_failed": failed,
                            "chosen_threshold": chosen, "warnings_at_chosen": warn_reasons, "note": "development split only; the test split is never used here"}, "rows": rows}, f, indent=2)
    with open(os.path.join(out_dir, "sweep.svg"), "w") as f:
        f.write(chart_svg(rows, chosen, args.lang))
    lines = [f"# Threshold sweep, {args.lang} (development split, seed {args.seed}, {len(dev)} cases, {failed} Decider failures)", "",
             f"Threshold fixed by `calibrate_threshold` on this split: **{chosen:g}**.", "",
             f"Warnings at that threshold, by reason: {', '.join(f'{k} {v}' for k, v in warn_reasons.items()) or 'none'}.", "",
             "| threshold | decisive answers | right when decisive | 3-way accuracy | mean utility |", "|---|---|---|---|---|"]
    for r in rows:
        acc = "n/a" if r["decisive_accuracy"] is None else f"{r['decisive_accuracy']:.3f}"
        lines.append(f"| {r['threshold']:g}{' (chosen)' if r['threshold'] == chosen else ''} | {r['coverage']:.3f} | {acc} | {r['action_accuracy']:.3f} | {r['mean_utility']:.3f} |")
    with open(os.path.join(out_dir, "sweep.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
