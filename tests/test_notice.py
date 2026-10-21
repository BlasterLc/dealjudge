from datetime import date, timedelta

from dealjudge.agent import build_tools
from dealjudge.handler import VerdictLog
from dealjudge.history import PricePoint, compute_stats
from dealjudge.judge import Judgement
from dealjudge.notice import template_notice, write_notice
from dealjudge.policy import Decision

END = date(2026, 10, 20)
PRICES = [40000] * 85 + [32000]
STATS = compute_stats([PricePoint(END - timedelta(days=len(PRICES) - 1 - i), p) for i, p in enumerate(PRICES)])


def judgement(action):
    return Judgement(0.9, "good", 0.9, 0.9, Decision(action, 0.9, "motivo"), 5.0, False)


class FakeBedrock:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.prompts = text, error, []

    def converse(self, **kwargs):
        self.prompts.append(kwargs["messages"][0]["content"][0]["text"])
        if self.error:
            raise self.error
        return {"output": {"message": {"content": [{"text": self.text}]}}}


def test_template_notice_has_the_figures_and_the_warning_only_when_needed():
    ok = template_notice(judgement("alert"), STATS, "Audifonos Aura X2")
    assert "$32.000" in ok and "$40.000" in ok and "20" in ok
    assert "cautela" not in ok.lower()
    assert "cautela" in template_notice(judgement("alert_with_warning"), STATS, "Audifonos Aura X2").lower()


def test_write_notice_uses_the_model_text_and_gives_it_the_figures():
    client = FakeBedrock("Bajó a $32.000, 20 % bajo lo habitual.")
    assert write_notice(judgement("alert"), STATS, "Audifonos Aura X2", client) == "Bajó a $32.000, 20 % bajo lo habitual."
    assert "$32.000" in client.prompts[0] and "$40.000" in client.prompts[0]


def test_write_notice_falls_back_to_the_template_when_bedrock_fails():
    text = write_notice(judgement("alert"), STATS, "Audifonos Aura X2", FakeBedrock(error=RuntimeError("throttled")))
    assert "$32.000" in text


def test_enviar_aviso_tool_sends_the_notice_for_a_logged_verdict():
    log, outbox = VerdictLog(), []
    log["o1"] = (judgement("alert"), STATS)
    tools = build_tools(log, outbox, bedrock_client=FakeBedrock("Aviso listo."))
    result = tools["send_alert"]("o1", "Audifonos Aura X2", 32000)
    assert result == "Aviso listo."
    assert outbox == [{"offer_id": "o1", "product": "Audifonos Aura X2", "action": "alert", "notice": "Aviso listo."}]
