"""The three typed questions Decider answers about each offer, in one round trip."""

from typing import Any

from dealjudge import i18n


def decider_questions(lang: str = i18n.DEFAULT_LANG) -> dict[str, dict[str, Any]]:
    t = lambda name: i18n.text(lang, name)  # noqa: E731
    return {
        "is_real": {
            "type": "noul",
            "instructions": t("q_is_real"),
            "criteria": {"true": t("q_is_real_true"), "false": t("q_is_real_false")},
        },
        "level": {
            "type": "choice",
            "instructions": t("q_level"),
            "criteria": i18n.level_criteria(lang),
        },
        "fits_user": {
            "type": "noul",
            "instructions": t("q_fits"),
            "criteria": {"true": t("q_fits_true"), "false": t("q_fits_false")},
        },
    }
