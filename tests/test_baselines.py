import json

from dealjudge.baselines import LlmJudge, cyber_watch_rule


def test_rule_alerts_on_a_20_percent_drop_and_not_on_19():
    assert cyber_watch_rule(100, 80) == "alert"
    assert cyber_watch_rule(100, 81) == "stay_silent"


def test_rule_ignores_a_missing_previous_price():
    assert cyber_watch_rule(0, 50) == "stay_silent"


class FakeBedrock:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.calls = text, error, []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {
            "output": {"message": {"content": [{"text": self.text}]}},
            "usage": {"inputTokens": 321, "outputTokens": 17},
            "metrics": {"latencyMs": 480},
        }


VALID = json.dumps({"is_real": True, "level": "good", "fits_user": False})


def test_llm_judge_parses_json_inside_a_code_fence():
    client = FakeBedrock("```json\n" + VALID + "\n```")
    j = LlmJudge(client=client).judge("estado")
    assert (j.is_real, j.level, j.fits_user) == (True, "good", False)
    assert (j.input_tokens, j.output_tokens, j.latency_ms) == (321, 17, 480)
    assert j.failed is False
    call = client.calls[0]
    assert call["modelId"] == "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    assert call["inferenceConfig"]["temperature"] == 0


def test_llm_judge_marks_invalid_json_as_failed():
    assert LlmJudge(client=FakeBedrock("no sé")).judge("estado").failed is True


def test_llm_judge_marks_an_unknown_level_as_failed():
    text = json.dumps({"is_real": True, "level": "genial", "fits_user": True})
    assert LlmJudge(client=FakeBedrock(text)).judge("estado").failed is True


def test_llm_judge_marks_a_client_error_as_failed():
    assert LlmJudge(client=FakeBedrock(error=RuntimeError("throttled"))).judge("estado").failed is True
