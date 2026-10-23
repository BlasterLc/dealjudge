"""Latency and cost of Decider (local) against the Bedrock LLM judge, on the same states.

Usage: AWS_PROFILE=<profile> python scripts/bench_latency_cost.py [--lang en|es] [--n 10] [--seed 101]

Uses the dev seed (not the test seed) so it never touches the evaluation's test cases. Calls are
sequential, after a few warm-up calls that are not counted, in two separate phases (all Decider calls, then
all LLM calls): interleaving them lets the laptop GPU drop its clock during the slow LLM calls and inflates
Decider's latency. The LLM client has retries off, so a call either succeeds (and is timed) or is counted as
failed: with the default retries a throttled call is silently retried and its wall clock hides the throttling.
Wall-clock time is measured around each call from this process (what a caller waits); the service-reported
time is kept next to it.
Writes results/bench/<lang>/latency_cost.{json,md}.
"""

import argparse
import json
import os
import statistics
import time

import boto3
from botocore.config import Config

from dealjudge import i18n
from dealjudge.baselines import LlmJudge
from dealjudge.client import DeciderClient
from dealjudge.evaluate import LLM_PRICE_USD_PER_MTOK, llm_cost_usd
from dealjudge.generator import generate_cases
from dealjudge.history import compute_stats, fits_profile, render_state
from dealjudge.judge import Judge

WARMUP = 3


def summary(values):
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "median_ms": round(statistics.median(ordered), 1),
        "mean_ms": round(statistics.fmean(ordered), 1),
        "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 1),
        "max_ms": round(ordered[-1], 1),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=i18n.LANGS, default=i18n.DEFAULT_LANG)
    ap.add_argument("--n", type=int, default=10, help="cases per scenario")
    ap.add_argument("--seed", type=int, default=101)
    args = ap.parse_args()

    cases = generate_cases(args.n, args.seed)
    prepared = []
    for case in cases:
        stats = compute_stats(case.series)
        state = render_state(i18n.product_name(args.lang, case.product), stats, case.advertised_list_price, case.profile, args.lang)
        prepared.append((state, stats.days_of_history, fits_profile(stats, case.profile)))

    decider = Judge(DeciderClient(), lang=args.lang)
    llm_client = boto3.client("bedrock-runtime", region_name="us-east-1", config=Config(retries={"max_attempts": 1, "mode": "standard"}, read_timeout=30, connect_timeout=10))
    llm = LlmJudge(lang=args.lang, client=llm_client)

    for state, days, fits in prepared[:WARMUP]:
        decider.judge(state, days, fits)
    d_wall, d_server, d_failed = [], [], 0
    for state, days, fits in prepared:
        t = time.perf_counter()
        j = decider.judge(state, days, fits)
        wall = (time.perf_counter() - t) * 1000
        if j.failed:
            d_failed += 1
        else:
            d_wall.append(wall)
            if j.latency_ms is not None:
                d_server.append(j.latency_ms)

    for state, days, fits in prepared[:WARMUP]:  # opens the connection; throttled warm-ups are fine
        llm.judge(state)
    l_wall, l_server, l_failed, in_tok, out_tok = [], [], 0, 0, 0
    for state, days, fits in prepared:
        t = time.perf_counter()
        r = llm.judge(state)
        wall = (time.perf_counter() - t) * 1000
        if r.failed:
            l_failed += 1
        else:
            l_wall.append(wall)
            l_server.append(r.latency_ms)
            in_tok += r.input_tokens
            out_tok += r.output_tokens

    ok = len(l_wall)
    per_1000 = llm_cost_usd(in_tok, out_tok) / ok * 1000 if ok else None
    result = {
        "meta": {
            "lang": args.lang, "seed": args.seed, "cases": len(prepared), "warmup_calls": WARMUP,
            "llm_model": llm.model_id, "llm_price_usd_per_mtok": LLM_PRICE_USD_PER_MTOK,
            "decider_checkpoint": "StrandsAgents/strands-decider-2B-hobson-v19", "decider_host": "local GPU (laptop RTX 4050)",
            "note": "sequential calls on simulated states, Decider and LLM in separate phases; the LLM is called from this machine over the internet with retries off (failed = throttled or errored)",
            "price_note": "LLM price is the public list price used by the evaluation; verify before quoting.",
        },
        "decider": {"wall_clock": summary(d_wall), "server_reported": summary(d_server) if d_server else None, "failed": d_failed, "api_cost_usd_per_1000": 0.0},
        "llm": {
            "wall_clock": summary(l_wall) if l_wall else None, "bedrock_reported": summary(l_server) if l_server else None,
            "failed": l_failed, "failed_rate": round(l_failed / len(prepared), 3), "avg_input_tokens": round(in_tok / ok) if ok else None, "avg_output_tokens": round(out_tok / ok) if ok else None,
            "cost_usd_per_1000": round(per_1000, 4) if per_1000 is not None else None,
        },
    }
    out_dir = os.path.join("results", "bench", args.lang)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "latency_cost.json"), "w") as f:
        json.dump(result, f, indent=2)

    dw, lw = result["decider"]["wall_clock"], result["llm"]["wall_clock"]
    lines = [
        f"# Latency and cost, {args.lang} (simulated states, dev seed {args.seed}, {len(prepared)} cases)",
        "",
        "| | Decider 2B (local GPU) | " + llm.model_id.split(".")[-1] + " (Bedrock) |",
        "|---|---|---|",
        f"| median, wall clock (ms) | {dw['median_ms']} | {lw['median_ms'] if lw else 'n/a'} |",
        f"| p95, wall clock (ms) | {dw['p95_ms']} | {lw['p95_ms'] if lw else 'n/a'} |",
        f"| max, wall clock (ms) | {dw['max_ms']} | {lw['max_ms'] if lw else 'n/a'} |",
        f"| failed calls (LLM: no retries) | {d_failed} of {len(prepared)} | {l_failed} of {len(prepared)} |",
        f"| API cost per 1,000 decisions (USD) | 0 | {result['llm']['cost_usd_per_1000']} |",
        f"| tokens per decision (in / out) | n/a | {result['llm']['avg_input_tokens']} / {result['llm']['avg_output_tokens']} |",
        "",
        "Decider's cost is your own GPU time (not counted here). Both ask the same three questions on the same state.",
        "The LLM latency is for calls that succeeded and includes the network; Decider ran on the same machine as this script.",
        "Failed LLM calls are Bedrock rate limits (ThrottlingException) on this account at a sequential pace; with default retries they are retried and cost seconds instead.",
    ]
    with open(os.path.join(out_dir, "latency_cost.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
