"""The two competitors Decider is measured against.

- ``cyber_watch_rule``: the rule the original price watcher used (alert on a drop of at
  least 20 % from the last seen price). It sees two prices and nothing else.
- ``LlmJudge``: a Bedrock model given the same state and the same three questions.
"""

import json
import re
from dataclasses import dataclass

from dealjudge import i18n

DEFAULT_LLM = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def cyber_watch_rule(prev_price: int, price: int, drop_pct: float = 20.0) -> str:
    if prev_price <= 0:
        return "stay_silent"
    return "alert" if price <= prev_price * (1 - drop_pct / 100) else "stay_silent"


@dataclass(frozen=True)
class LlmJudgement:
    is_real: bool
    level: str
    fits_user: bool
    input_tokens: int
    output_tokens: int
    latency_ms: float
    failed: bool


_FAILED = LlmJudgement(False, "", False, 0, 0, 0.0, True)

def _parse(text: str, lang: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    data = json.loads(match.group(0))
    level = i18n.level_from_key(lang, data["level"])
    if level is None or not isinstance(data["is_real"], bool) or not isinstance(data["fits_user"], bool):
        raise ValueError("unexpected answer")
    return {**data, "level": level}


class LlmJudge:
    def __init__(self, model_id: str = DEFAULT_LLM, region: str = "us-east-1", client=None, lang: str = i18n.DEFAULT_LANG) -> None:
        self.model_id = model_id
        self.lang = lang
        if client is None:
            import boto3

            client = boto3.client("bedrock-runtime", region_name=region)
        self._client = client

    def judge(self, state: str) -> LlmJudgement:
        levels = "\n".join(f"   - {name}: {desc}" for name, desc in i18n.level_criteria(self.lang).items())
        prompt = i18n.text(self.lang, "llm_prompt", state=state, levels=levels)
        try:
            response = self._client.converse(
                modelId=self.model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 100, "temperature": 0},
            )
            data = _parse(response["output"]["message"]["content"][0]["text"], self.lang)
            usage = response.get("usage", {})
            return LlmJudgement(
                data["is_real"],
                data["level"],
                data["fits_user"],
                int(usage.get("inputTokens", 0)),
                int(usage.get("outputTokens", 0)),
                float(response.get("metrics", {}).get("latencyMs", 0.0)),
                False,
            )
        except Exception:  # the baseline must never take the evaluation down
            return _FAILED
