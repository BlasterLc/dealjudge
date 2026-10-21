import json

from dealjudge.demo import DEMO_SCENARIOS, build_demo
from dealjudge.judge import Judgement
from dealjudge.policy import Decision

KEYS = {"id", "product", "store_label", "series", "baseline_median", "current", "advertised_list_price",
        "stats", "verdict", "notice"}


class FakeJudge:
    threshold = 0.25

    def judge(self, state, history_days, fits_user=None):
        action = "avisar_con_advertencia" if history_days < 14 else ("avisar" if fits_user else "callar")
        return Judgement(0.9, "buena", 0.5, 0.9, Decision(action, 0.5, "motivo"), 5.0, False)


class NoBedrock:
    def converse(self, **kwargs):
        raise RuntimeError("sin AWS")


def build(tmp_path):
    out = tmp_path / "demo.json"
    build_demo(7, str(out), judge=FakeJudge(), bedrock_client=NoBedrock())
    return json.loads(out.read_text())


def test_demo_has_six_cases_covering_the_three_behaviours(tmp_path):
    cases = build(tmp_path)["cases"]
    assert len(cases) == 6
    scenarios = {c["scenario"] for c in cases}
    assert {"pico_inflado", "baja_genuina", "historial_corto"} <= scenarios
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
