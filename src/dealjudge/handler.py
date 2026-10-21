"""A Strands InterventionHandler that judges an offer before the alert tool runs.

``before_tool_call`` runs before ``send_alert`` executes. It rebuilds the price history
of the offer, asks the judge, and maps the action to the SDK:

- alert / alert_with_warning -> Proceed (the verdict is kept for the notice)
- stay_silent                          -> Deny
- the same offer at the same price and action already announced -> Deny (no spam)

The model is never the gate: Decider measures, ``decide`` in policy.py decides.
"""

import asyncio
from collections.abc import Callable, Sequence
from typing import Any

from strands.interventions import Deny, InterventionHandler, Proceed

from dealjudge import i18n
from dealjudge.history import HistoryStats, PricePoint, UserProfile, compute_stats, fits_profile, render_state
from dealjudge.judge import Judge, Judgement

TOOL_NAME = "send_alert"

Source = Callable[[str], tuple[Sequence[PricePoint], int | None]]
"""offer_id -> (price series, advertised list price or None). Raises KeyError if unknown."""


class VerdictLog(dict):
    """offer_id -> (Judgement, HistoryStats) for every alert that was allowed through."""


class AlertLedger:
    """Remembers the last (price, action) announced per offer, so the same alert is not repeated."""

    def __init__(self) -> None:
        self._last: dict[str, tuple[int, str]] = {}

    def should_notify(self, offer_id: str, price: int, action: str) -> bool:
        key = (price, action)
        if self._last.get(offer_id) == key:
            return False
        self._last[offer_id] = key
        return True


class DealjudgeHandler(InterventionHandler):
    name = "dealjudge"

    def __init__(self, judge: Judge, source: Source, profile: UserProfile, log: VerdictLog, ledger: AlertLedger) -> None:
        self._judge, self._source, self._profile, self._log, self._ledger = judge, source, profile, log, ledger

    async def before_tool_call(self, event: Any, **kwargs: Any) -> Proceed | Deny:
        tool_use = getattr(event, "tool_use", None) or {}
        if tool_use.get("name") != TOOL_NAME:
            return Proceed()
        args = tool_use.get("input") or {}
        offer_id, product = str(args.get("offer_id") or ""), str(args.get("product") or "")
        try:
            series, advertised = self._source(offer_id)
            stats: HistoryStats = compute_stats(series)
        except (KeyError, ValueError):
            return Deny(i18n.text(self._judge.lang, "deny_no_data"))
        lang = self._judge.lang
        state = render_state(product, stats, advertised, self._profile, lang)
        judgement: Judgement = await asyncio.to_thread(
            self._judge.judge, state, stats.days_of_history, fits_profile(stats, self._profile)
        )
        action = judgement.decision.action
        if action == "stay_silent":
            return Deny(i18n.reason_text(lang, judgement.decision.reason))
        if not self._ledger.should_notify(offer_id, stats.current, action):
            return Deny(i18n.text(lang, "deny_repeat"))
        self._log[offer_id] = (judgement, stats)
        return Proceed()
