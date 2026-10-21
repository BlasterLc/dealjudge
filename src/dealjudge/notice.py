"""The text of an alert. Bedrock writes it, but only from figures the code hands over."""

from dealjudge import i18n
from dealjudge.history import HistoryStats
from dealjudge.judge import Judgement

NOTICE_MODEL = "amazon.nova-lite-v1:0"


def template_notice(judgement: Judgement, stats: HistoryStats, product: str, lang: str = i18n.DEFAULT_LANG) -> str:
    text = i18n.text(
        lang, "notice_template",
        product=product, price=i18n.money(lang, stats.current), pct=f"{stats.real_discount_pct:.0f}",
        median=i18n.money(lang, stats.baseline_median), minimum=i18n.money(lang, stats.min_price),
    )
    if judgement.decision.action == "alert_with_warning":
        text += i18n.text(lang, "notice_caution", reason=i18n.reason_text(lang, judgement.decision.reason))
    return text


def write_notice(
    judgement: Judgement, stats: HistoryStats, product: str, bedrock_client=None, lang: str = i18n.DEFAULT_LANG
) -> str:
    warning = ""
    if judgement.decision.action == "alert_with_warning":
        warning = i18n.text(lang, "notice_warning", reason=i18n.reason_text(lang, judgement.decision.reason))
    prompt = i18n.text(
        lang, "notice_prompt",
        product=product, price=i18n.money(lang, stats.current), median=i18n.money(lang, stats.baseline_median),
        pct=f"{stats.real_discount_pct:.0f}", minimum=i18n.money(lang, stats.min_price), warning=warning,
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
    return template_notice(judgement, stats, product, lang)
