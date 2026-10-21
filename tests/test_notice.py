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
    return Judgement(0.9, "good", 0.9, 0.9, Decision(action, 0.9, "short_history"), 5.0, False)


class FakeBedrock:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.prompts = text, error, []

    def converse(self, **kwargs):
        self.prompts.append(kwargs["messages"][0]["content"][0]["text"])
        if self.error:
            raise self.error
        return {"output": {"message": {"content": [{"text": self.text}]}}}


def test_template_notice_has_the_figures_and_the_warning_only_when_needed():
    ok = template_notice(judgement("alert"), STATS, "Aura X2 headphones")
    assert "CLP 32,000" in ok and "CLP 40,000" in ok and "20%" in ok
    assert "careful" not in ok.lower()
    warned = template_notice(judgement("alert_with_warning"), STATS, "Aura X2 headphones")
    assert "careful" in warned.lower() and "little price history" in warned


def test_template_notice_in_spanish_uses_spanish_words_and_pesos():
    text = template_notice(judgement("alert_with_warning"), STATS, "Audífonos Aura X2", lang="es")
    assert "$32.000" in text and "ahora" in text and "Ten cautela" in text and "poco historial" in text
    assert "now" not in text and "CLP" not in text


def test_write_notice_uses_the_model_text_and_gives_it_the_figures():
    client = FakeBedrock("Dropped to CLP 32,000, 20% below usual.")
    assert write_notice(judgement("alert"), STATS, "Aura X2 headphones", client) == "Dropped to CLP 32,000, 20% below usual."
    assert "CLP 32,000" in client.prompts[0] and "CLP 40,000" in client.prompts[0]
    assert "in English" in client.prompts[0]


def test_write_notice_asks_for_spanish_in_the_spanish_version():
    client = FakeBedrock("Bajó a $32.000.")
    write_notice(judgement("alert"), STATS, "Audífonos Aura X2", client, lang="es")
    assert "en español" in client.prompts[0] and "$32.000" in client.prompts[0]


def test_write_notice_falls_back_to_the_template_when_bedrock_fails():
    text = write_notice(judgement("alert"), STATS, "Aura X2 headphones", FakeBedrock(error=RuntimeError("throttled")))
    assert "CLP 32,000" in text


def test_send_alert_tool_sends_the_notice_for_a_logged_verdict():
    log, outbox = VerdictLog(), []
    log["o1"] = (judgement("alert"), STATS)
    tools = build_tools(log, outbox, bedrock_client=FakeBedrock("Notice ready."))
    result = tools["send_alert"]("o1", "Aura X2 headphones", 32000)
    assert result == "Notice ready."
    assert outbox == [{"offer_id": "o1", "product": "Aura X2 headphones", "action": "alert", "notice": "Notice ready."}]


def test_send_alert_tool_without_a_verdict_says_so_in_the_chosen_language():
    assert build_tools(VerdictLog(), [], lang="en")["send_alert"]("x", "p", 1) == "No verdict for that offer."
    assert build_tools(VerdictLog(), [], lang="es")["send_alert"]("x", "p", 1) == "Sin veredicto para esa oferta."
