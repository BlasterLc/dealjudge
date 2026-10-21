"""The confidence rule: plain Python that turns Decider's answers into an action.

The model is never the gate. Decider measures; this function decides. It is pure and
has no SDK import, so a logged answer can be replayed later against any threshold.

Precedence (first match wins):
1. a malformed number or an unknown level   -> avisar_con_advertencia
2. fewer than 14 days of history            -> avisar_con_advertencia
3. confidence below the threshold           -> avisar_con_advertencia
4. confident, real, good level, fits user   -> avisar
5. confident and anything else              -> callar
"""

import math
from dataclasses import dataclass

from dealjudge.levels import LEVELS

ACTIONS = ("avisar", "callar", "avisar_con_advertencia")
DEFAULT_THRESHOLD = 0.70
MIN_HISTORY_DAYS = 14
GOOD_LEVELS = ("buena", "muy_buena", "excepcional")


@dataclass(frozen=True)
class Decision:
    action: str
    confidence: float
    reason: str


def _warn(reason: str, confidence: float = 0.0) -> Decision:
    return Decision("avisar_con_advertencia", confidence, reason)


def _valid(p: float) -> bool:
    return math.isfinite(p) and 0.0 <= p <= 1.0


def decide(
    is_real_p: float,
    level: str,
    level_conf: float,
    fits_p: float,
    history_days: int,
    threshold: float = DEFAULT_THRESHOLD,
) -> Decision:
    """Map one set of Decider answers to an action.

    Confidence is the lowest of the three answers' confidences; a yes/no answer with
    probability p has confidence max(p, 1 - p).
    """
    if not (_valid(is_real_p) and _valid(level_conf) and _valid(fits_p)):
        return _warn("No pude leer con seguridad la respuesta del modelo.")
    if level not in LEVELS:
        return _warn("No pude clasificar el nivel de la oferta.")
    confidence = min(max(is_real_p, 1 - is_real_p), level_conf, max(fits_p, 1 - fits_p))
    if history_days < MIN_HISTORY_DAYS:
        return _warn("Hay poco historial de precios para juzgar.", confidence)
    if confidence < threshold:
        return _warn("No estoy seguro de este veredicto.", confidence)
    if is_real_p >= 0.5 and level in GOOD_LEVELS and fits_p >= 0.5:
        return Decision("avisar", confidence, "Descuento real que cumple lo que pides.")
    return Decision("callar", confidence, "No es una oferta real o no cumple lo que pides.")
