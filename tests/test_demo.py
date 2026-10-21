import json

from dealjudge.demo import DEMO_SCENARIOS, build_demo
from dealjudge.judge import Judgement
from dealjudge.policy import Decision

KEYS = {"id", "product", "store_label", "series", "baseline_median", "current", "advertised_list_price",
        "stats", "verdict", "notice"}


class FakeJudge:
    threshold = 0.25

    def __init__(self, lang="en"):
        self.lang = lang

    def judge(self, state, history_days, fits_user=None):
        action = "alert_with_warning" if history_days < 14 else ("alert" if fits_user else "stay_silent")
        return Judgement(0.9, "good", 0.5, 0.9, Decision(action, 0.5, "short_history"), 5.0, False)


class NoBedrock:
    def converse(self, **kwargs):
        raise RuntimeError("no AWS")


def build(tmp_path, lang="en"):
    out = tmp_path / f"demo.{lang}.json"
    build_demo(7, str(out), judge=FakeJudge(lang), bedrock_client=NoBedrock())
    return json.loads(out.read_text())


def test_demo_has_six_cases_covering_the_three_behaviours(tmp_path):
    cases = build(tmp_path)["cases"]
    assert len(cases) == 6
    scenarios = {c["scenario"] for c in cases}
    assert {"inflated_spike", "genuine_drop", "short_history"} <= scenarios
    assert set(DEMO_SCENARIOS) == scenarios


def test_every_case_has_the_contract_keys_and_integer_prices(tmp_path):
    for c in build(tmp_path)["cases"]:
        assert KEYS <= set(c)
        assert all(isinstance(p["price"], int) for p in c["series"])
        assert isinstance(c["current"], int) and isinstance(c["baseline_median"], int)
        assert {"action", "level", "confidence", "reason"} <= set(c["verdict"])
        assert c["notice"]


def test_store_labels_are_fictional_and_the_file_says_it_is_simulated(tmp_path):
    data = build(tmp_path)
    assert data["simulated"] is True
    assert data["threshold"] == 0.25
    labels = {c["store_label"] for c in data["cases"]}
    assert labels and not labels & {"Falabella", "Paris", "Sodimac", "Lider", "Amazon", "Ripley"}


def test_each_language_gets_its_own_product_names_reasons_and_notices(tmp_path):
    en, es = build(tmp_path, "en"), build(tmp_path, "es")
    assert en["lang"] == "en" and es["lang"] == "es"
    silent_en = next(c for c in en["cases"] if c["verdict"]["action"] == "stay_silent")
    silent_es = next(c for c in es["cases"] if c["verdict"]["action"] == "stay_silent")
    assert silent_en["notice"].startswith("No alert sent.")
    assert silent_es["notice"].startswith("No se avisó.")
    assert silent_en["verdict"]["reason"] == "There is little price history to judge."
    assert silent_es["verdict"]["reason"] == "Hay poco historial de precios para juzgar."
    assert silent_en["verdict"]["reason_code"] == silent_es["verdict"]["reason_code"] == "short_history"
    assert {c["product"] for c in es["cases"]} != {c["product"] for c in en["cases"]}
