import asyncio
from datetime import date, timedelta
from types import SimpleNamespace

from strands.interventions import Deny, Proceed

from dealjudge.handler import AlertLedger, DealjudgeHandler, VerdictLog
from dealjudge.history import PricePoint, UserProfile
from dealjudge.judge import Judgement
from dealjudge.policy import Decision

END = date(2026, 10, 20)
PRICES = [40000] * 85 + [32000]
SERIES = [PricePoint(END - timedelta(days=len(PRICES) - 1 - i), p) for i, p in enumerate(PRICES)]


class FakeJudge:
    def __init__(self, action):
        self.action, self.calls = action, []

    def judge(self, state, history_days, fits_user=None):
        self.calls.append((state, history_days, fits_user))
        return Judgement(0.9, "good", 0.9, 0.9, Decision(self.action, 0.9, "motivo"), 5.0, False)


def source(offer_id):
    if offer_id == "desconocida":
        raise KeyError(offer_id)
    return SERIES, None


def event(name="send_alert", **tool_input):
    tool_input = tool_input or {"offer_id": "o1", "product": "Audifonos Aura X2", "price": 32000}
    return SimpleNamespace(tool_use={"name": name, "input": tool_input, "toolUseId": "t1"}, agent=SimpleNamespace(messages=[]))


def run(handler, ev):
    return asyncio.run(handler.before_tool_call(ev))


def make(action):
    judge, log = FakeJudge(action), VerdictLog()
    return DealjudgeHandler(judge, source, UserProfile(), log, AlertLedger()), judge, log


def test_alerting_verdict_proceeds_and_is_logged():
    handler, judge, log = make("alert")
    assert isinstance(run(handler, event()), Proceed)
    assert log["o1"][0].decision.action == "alert"
    assert judge.calls[0][2] is True  # fit with the profile was computed in code


def test_warning_verdict_proceeds_and_keeps_the_verdict_for_the_notice():
    handler, _, log = make("alert_with_warning")
    assert isinstance(run(handler, event()), Proceed)
    assert log["o1"][0].decision.action == "alert_with_warning"


def test_silent_verdict_denies_the_tool_call():
    handler, _, _ = make("stay_silent")
    result = run(handler, event())
    assert isinstance(result, Deny)
    assert result.reason


def test_same_offer_at_the_same_price_is_not_announced_twice():
    handler, _, _ = make("alert")
    assert isinstance(run(handler, event()), Proceed)
    assert isinstance(run(handler, event()), Deny)


def test_a_new_price_for_the_same_offer_is_announced_again():
    handler, _, _ = make("alert")
    assert isinstance(run(handler, event()), Proceed)
    changed = event(offer_id="o1", product="Audifonos Aura X2", price=30000)
    handler._source = lambda offer_id: (SERIES[:-1] + [PricePoint(END, 30000)], None)
    assert isinstance(run(handler, changed), Proceed)


def test_other_tools_pass_through_without_asking_the_judge():
    handler, judge, _ = make("stay_silent")
    assert isinstance(run(handler, event(name="otra_herramienta", x=1)), Proceed)
    assert judge.calls == []


def test_unknown_offer_is_denied_without_crashing():
    handler, judge, _ = make("alert")
    assert isinstance(run(handler, event(offer_id="desconocida", product="x", price=1)), Deny)
    assert judge.calls == []
