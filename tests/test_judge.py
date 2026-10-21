from dealjudge.client import DeciderResult, DeciderUnavailable
from dealjudge.judge import Judge
from dealjudge.policy import decide


class FakeClient:
    def __init__(self, answers=None, error=None, latency_ms=12.0):
        self.answers, self.error, self.latency_ms = answers, error, latency_ms
        self.calls = []

    def ask(self, state, questions):
        self.calls.append((state, questions))
        if self.error:
            raise self.error
        return DeciderResult(self.answers, self.latency_ms)


GOOD = {
    "is_real": {"type": "noul", "noul": 0.95},
    "level": {"type": "choice", "choice": "buena", "probabilities": {"buena": 0.8}, "confidence": 0.9},
    "fits_user": {"type": "noul", "noul": 0.9},
}


def test_judgement_maps_the_answers_through_the_policy():
    client = FakeClient(GOOD)
    j = Judge(client).judge("estado", 90)
    assert (j.is_real_p, j.level, j.level_conf, j.fits_p) == (0.95, "buena", 0.9, 0.9)
    assert j.level_prob == 0.8
    assert j.decision == decide(0.95, "buena", 0.9, 0.9, 90)
    assert j.latency_ms == 12.0
    assert j.failed is False
    assert len(client.calls) == 1
    assert set(client.calls[0][1]) == {"is_real", "level", "fits_user"}


def test_unavailable_decider_warns_instead_of_raising():
    j = Judge(FakeClient(error=DeciderUnavailable("down"))).judge("estado", 90)
    assert j.failed is True
    assert j.decision.action == "avisar_con_advertencia"


def test_missing_level_answer_warns():
    answers = {k: v for k, v in GOOD.items() if k != "level"}
    j = Judge(FakeClient(answers)).judge("estado", 90)
    assert j.failed is True
    assert j.decision.action == "avisar_con_advertencia"


def test_non_numeric_confidence_warns():
    answers = {**GOOD, "level": {**GOOD["level"], "confidence": "alta"}}
    j = Judge(FakeClient(answers)).judge("estado", 90)
    assert j.failed is True
    assert j.decision.action == "avisar_con_advertencia"


def test_code_computed_fit_overrides_the_models_answer():
    wrong_fit = {**GOOD, "fits_user": {"type": "noul", "noul": 0.1}}
    j = Judge(FakeClient(wrong_fit)).judge("estado", 90, fits_user=True)
    assert j.fits_p == 0.1  # the model's own answer is still recorded
    assert j.effective_fits_p == 1.0
    assert j.decision.action == "avisar"
    assert Judge(FakeClient(GOOD)).judge("estado", 90, fits_user=False).decision.action == "callar"
