"""The two competitors Decider is measured against.

- ``cyber_watch_rule``: the rule the original price watcher used (alert on a drop of at
  least 20 % from the last seen price). It sees two prices and nothing else.
- ``LlmJudge``: a Bedrock model given the same state and the same three questions.
"""

import json
import re
from dataclasses import dataclass

from dealjudge.levels import LEVELS
from dealjudge.questions import LEVEL_CRITERIA

DEFAULT_LLM = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def cyber_watch_rule(prev_price: int, price: int, drop_pct: float = 20.0) -> str:
    if prev_price <= 0:
        return "callar"
    return "avisar" if price <= prev_price * (1 - drop_pct / 100) else "callar"


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

_PROMPT = """Eres un juez de ofertas. Lees el estado de un producto y respondes tres preguntas.

{state}

Preguntas:
1. is_real (true/false): ¿es real este descuento? Es real si el precio actual está al menos \
10 % bajo la mediana de los 90 días anteriores a cualquier subida reciente.
2. level: ¿qué nivel de oferta es? Elige uno:
{levels}
3. fits_user (true/false): ¿cumple lo que pide el usuario? Debe estar dentro de su tope de precio, \
si lo tiene, y alcanzar el nivel mínimo que pide.

Responde SOLO con un objeto JSON: {{"is_real": bool, "level": str, "fits_user": bool}}"""


def _parse(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    data = json.loads(match.group(0))
    if data["level"] not in LEVELS or not isinstance(data["is_real"], bool) or not isinstance(data["fits_user"], bool):
        raise ValueError("unexpected answer")
    return data


class LlmJudge:
    def __init__(self, model_id: str = DEFAULT_LLM, region: str = "us-east-1", client=None) -> None:
        self.model_id = model_id
        if client is None:
            import boto3

            client = boto3.client("bedrock-runtime", region_name=region)
        self._client = client

    def judge(self, state: str) -> LlmJudgement:
        levels = "\n".join(f"   - {name}: {desc}" for name, desc in LEVEL_CRITERIA.items())
        prompt = _PROMPT.format(state=state, levels=levels)
        try:
            response = self._client.converse(
                modelId=self.model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 100, "temperature": 0},
            )
            data = _parse(response["output"]["message"]["content"][0]["text"])
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
