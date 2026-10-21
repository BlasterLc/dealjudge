"""The Strands agent: one tool, ``send_alert``, guarded by DealjudgeHandler."""

from collections.abc import Callable

from dealjudge import i18n
from dealjudge.handler import DealjudgeHandler, VerdictLog
from dealjudge.notice import write_notice


def build_tools(log: VerdictLog, outbox: list, bedrock_client=None, lang: str = i18n.DEFAULT_LANG) -> dict[str, Callable]:
    def send_alert(offer_id: str, product: str, price: int) -> str:
        """Send the user an alert about an offer.

        Args:
            offer_id: identifier of the offer to announce.
            product: name of the product.
            price: current price in CLP.
        """
        if offer_id not in log:
            return i18n.text(lang, "tool_no_verdict")
        judgement, stats = log[offer_id]
        notice = write_notice(judgement, stats, product, bedrock_client, lang)
        outbox.append({"offer_id": offer_id, "product": product, "action": judgement.decision.action, "notice": notice})
        return notice

    return {"send_alert": send_alert}


def build_agent(
    handler: DealjudgeHandler, log: VerdictLog, outbox: list, model=None, bedrock_client=None, lang: str = i18n.DEFAULT_LANG
):
    from strands import Agent, tool
    from strands.models import BedrockModel

    tools = build_tools(log, outbox, bedrock_client, lang)
    return Agent(
        model=model or BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1"),
        tools=[tool(tools["send_alert"])],
        interventions=[handler],
        system_prompt=i18n.text(lang, "agent_system"),
    )
