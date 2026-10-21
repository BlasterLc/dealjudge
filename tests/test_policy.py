import pytest

from dealjudge.policy import ACTIONS, DEFAULT_THRESHOLD, Decision, decide


def test_default_threshold_and_actions():
    assert DEFAULT_THRESHOLD == 0.70
    assert ACTIONS == ("alert", "stay_silent", "alert_with_warning")


def test_confident_real_good_offer_that_fits_alerts():
    assert decide(0.95, "good", 0.9, 0.9, 90).action == "alert"


def test_confident_fake_offer_stays_silent():
    assert decide(0.05, "no_deal", 0.9, 0.9, 90).action == "stay_silent"


def test_confident_offer_that_does_not_fit_stays_silent():
    assert decide(0.95, "very_good", 0.9, 0.1, 90).action == "stay_silent"


def test_marginal_level_stays_silent_even_when_confident():
    assert decide(0.95, "marginal", 0.9, 0.9, 90).action == "stay_silent"


def test_low_level_confidence_warns():
    assert decide(0.95, "good", 0.5, 0.9, 90).action == "alert_with_warning"


def test_unsure_is_real_warns():
    # confidence of a yes/no answer is max(p, 1 - p): 0.6 is below the threshold
    assert decide(0.6, "good", 0.9, 0.9, 90).action == "alert_with_warning"


def test_short_history_warns_even_when_everything_is_confident():
    assert decide(0.95, "good", 0.9, 0.9, 5).action == "alert_with_warning"


@pytest.mark.parametrize(
    "args",
    [
        (float("nan"), "good", 0.9, 0.9),
        (0.95, "good", float("nan"), 0.9),
        (0.95, "good", 0.9, 1.5),
        (-0.1, "good", 0.9, 0.9),
    ],
)
def test_invalid_numbers_warn(args):
    assert decide(*args, 90).action == "alert_with_warning"


def test_unknown_level_warns():
    assert decide(0.95, "legendaria", 0.9, 0.9, 90).action == "alert_with_warning"


def test_threshold_is_respected():
    assert decide(0.95, "good", 0.5, 0.9, 90, threshold=0.4).action == "alert"


def test_decision_carries_the_confidence_and_a_reason():
    d = decide(0.95, "good", 0.9, 0.8, 90)
    assert isinstance(d, Decision)
    assert d.confidence == pytest.approx(0.8)
    assert d.reason
