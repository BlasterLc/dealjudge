"""The judge: asks Decider the three questions and applies the confidence rule."""

import math
from dataclasses import dataclass

from dealjudge.client import DeciderClient, DeciderUnavailable
from dealjudge.policy import DEFAULT_THRESHOLD, Decision, decide
from dealjudge.questions import decider_questions


@dataclass(frozen=True)
class Judgement:
    is_real_p: float
    level: str
    level_conf: float
    fits_p: float
    decision: Decision
    latency_ms: float | None
    failed: bool
    level_prob: float = 0.0
    fits_used: float | None = None  # code-computed fit (1.0 / 0.0) when given; else the model's answer

    @property
    def effective_fits_p(self) -> float:
        return self.fits_p if self.fits_used is None else self.fits_used


class Judge:
    def __init__(self, client: DeciderClient, threshold: float = DEFAULT_THRESHOLD) -> None:
        self._client = client
        self.threshold = threshold

    def judge(self, state: str, history_days: int, fits_user: bool | None = None) -> Judgement:
        """Never raises: a Decider that does not answer yields a warning, not a crash.

        ``fits_user``, when given, is the code-computed fit with the user's profile; it replaces
        the model's own answer in the decision (which is still recorded).
        """
        try:
            result = self._client.ask(state, decider_questions())
            answers = result.answers
            level = str(answers["level"]["choice"])
            is_real_p = float(answers["is_real"]["noul"])
            level_conf = float(answers["level"]["confidence"])
            fits_p = float(answers["fits_user"]["noul"])
            level_prob = float(answers["level"].get("probabilities", {}).get(level, 0.0))
        except (DeciderUnavailable, KeyError, TypeError, ValueError, AttributeError):
            nan = math.nan
            decision = decide(nan, "", nan, nan, history_days, self.threshold)
            return Judgement(nan, "", nan, nan, decision, None, True)
        fits_used = None if fits_user is None else float(fits_user)
        decision = decide(
            is_real_p, level, level_conf, fits_p if fits_used is None else fits_used, history_days, self.threshold
        )
        return Judgement(is_real_p, level, level_conf, fits_p, decision, result.latency_ms, False, level_prob, fits_used)
