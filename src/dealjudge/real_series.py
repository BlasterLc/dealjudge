"""Real prices recorded by the price registrar (snapshot.py), as series the judge can read."""

import ast
import json
import sqlite3
from datetime import date

from dealjudge.history import PricePoint, UserProfile, compute_stats, render_state


def load_series(db_path: str, url: str) -> list[PricePoint]:
    """One CLP price per day for ``url``: the minimum seen that day."""
    db = sqlite3.connect(db_path)
    try:
        rows = db.execute(
            "SELECT substr(ts, 1, 10) AS day, MIN(price) FROM snapshots "
            "WHERE url = ? AND currency = 'CLP' GROUP BY day ORDER BY day",
            (url,),
        ).fetchall()
    finally:
        db.close()
    return [PricePoint(date.fromisoformat(day), int(price)) for day, price in rows]


def knasta_reference(extra_json: str | None) -> dict | None:
    """Knasta's own verdict stored in a row's ``extra`` column, or None if it is not there."""
    try:
        extra = json.loads(extra_json)
        descriptive = extra["descriptive"]
        if isinstance(descriptive, str):
            descriptive = ast.literal_eval(descriptive)
        return {
            "state": str(descriptive["state"]),
            "percent": float(extra["percent"]),
            "n_history": int(descriptive["n_history"]),
        }
    except (TypeError, ValueError, KeyError, SyntaxError):
        return None


def describe_real(db_path: str, judge, limit: int = 40) -> dict:
    """Run the judge on real recorded products and set the verdict beside Knasta's.

    There is no ground truth for real prices, so this is a side-by-side reference, not an
    accuracy figure.
    """
    db = sqlite3.connect(db_path)
    try:
        rows = db.execute(
            "SELECT url, title, product, extra FROM snapshots WHERE source = 'knasta' "
            "AND ts = (SELECT MAX(ts) FROM snapshots) LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        db.close()
    out = []
    for url, title, product, extra in rows:
        series = load_series(db_path, url)
        reference = knasta_reference(extra)
        if not series or reference is None:
            continue
        stats = compute_stats(series)
        j = judge.judge(render_state(title, stats, None, UserProfile(), judge.lang), stats.days_of_history)
        out.append(
            {
                "product": product,
                "title": title,
                "days_of_history": stats.days_of_history,
                "decider_action": j.decision.action,
                "decider_level": j.level,
                "knasta": reference,
            }
        )
    actions: dict[str, int] = {}
    for row in out:
        actions[row["decider_action"]] = actions.get(row["decider_action"], 0) + 1
    return {"n": len(out), "decider_actions": actions, "rows": out}
