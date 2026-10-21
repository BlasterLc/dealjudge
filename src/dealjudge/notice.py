"""The text of an alert. Bedrock writes it, but only from figures the code hands over."""

from dealjudge.history import HistoryStats
from dealjudge.judge import Judgement

NOTICE_MODEL = "amazon.nova-lite-v1:0"

_PROMPT = """Escribe un aviso de oferta de 2 o 3 frases en español, claro y sin exagerar.
Usa SOLO estas cifras, sin inventar otras:
- producto: {product}
- precio actual: {price}
- mediana de 90 días: {median}
- descuento real contra la mediana: {pct} %
- precio mínimo: {minimum}
{warning}
Responde solo con el texto del aviso."""


def _clp(n: int) -> str:
    return "$" + format(int(n), ",").replace(",", ".")


def template_notice(judgement: Judgement, stats: HistoryStats, product: str) -> str:
    text = (
        f"{product}: ahora {_clp(stats.current)}, {stats.real_discount_pct:.0f} % bajo la mediana de "
        f"90 días ({_clp(stats.baseline_median)}). Mínimo registrado: {_clp(stats.min_price)}."
    )
    if judgement.decision.action == "alert_with_warning":
        text += f" Ten cautela: {judgement.decision.reason}"
    return text


def write_notice(judgement: Judgement, stats: HistoryStats, product: str, bedrock_client=None) -> str:
    warning = ""
    if judgement.decision.action == "alert_with_warning":
        warning = f"- incluye una advertencia clara: {judgement.decision.reason}"
    prompt = _PROMPT.format(
        product=product,
        price=_clp(stats.current),
        median=_clp(stats.baseline_median),
        pct=f"{stats.real_discount_pct:.0f}",
        minimum=_clp(stats.min_price),
        warning=warning,
    )
    try:
        if bedrock_client is None:
            import boto3

            bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
        response = bedrock_client.converse(
            modelId=NOTICE_MODEL,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 200, "temperature": 0.2},
        )
        text = response["output"]["message"]["content"][0]["text"].strip()
        if text:
            return text
    except Exception:  # an alert must still go out if Bedrock is down
        pass
    return template_notice(judgement, stats, product)
