from dealjudge.generator import SCENARIOS, Truth, generate_cases, truth_for
from dealjudge.history import HistoryStats, UserProfile, compute_stats

GOOD = {"buena", "muy_buena", "excepcional"}


def stats_for(real_discount_pct, current=30000, days=90):
    return HistoryStats(
        current=current,
        baseline_median=int(current / (1 - real_discount_pct / 100)),
        min_price=current,
        days_of_history=days,
        days_since_last_drop=0,
        spike_recent=False,
        spike_peak=None,
        real_discount_pct=real_discount_pct,
    )


def cases_of(scenario, n=20, seed=3):
    return [c for c in generate_cases(n, seed) if c.scenario == scenario]


def test_generate_cases_is_deterministic_and_sized():
    a = generate_cases(5, seed=1)
    assert len(a) == 5 * len(SCENARIOS)
    assert a == generate_cases(5, seed=1)
    assert a != generate_cases(5, seed=2)


def test_inflated_spike_is_never_real():
    cases = cases_of("pico_inflado")
    assert cases
    for c in cases:
        assert c.truth.is_real is False
        assert c.advertised_list_price >= 1.2 * c.series[-1].price


def test_genuine_drop_is_real_with_a_good_level():
    cases = cases_of("baja_genuina")
    assert cases
    for c in cases:
        assert c.truth.is_real is True
        assert c.truth.level in GOOD


def test_limit_cases_sit_on_the_edge():
    for c in cases_of("limite_10"):
        assert 9.5 <= compute_stats(c.series).real_discount_pct <= 10.5
    for c in cases_of("limite_25"):
        assert 24.5 <= compute_stats(c.series).real_discount_pct <= 25.5


def test_short_history_warns():
    cases = cases_of("historial_corto")
    assert cases
    for c in cases:
        assert len(c.series) < 14
        assert c.truth.action == "avisar_con_advertencia"


def test_truth_alerts_on_a_real_discount_that_fits():
    truth = truth_for(stats_for(30.0), UserProfile(max_price=None, min_level="buena"), None)
    assert truth == Truth(is_real=True, level="muy_buena", fits_user=True, action="avisar")


def test_truth_is_silent_on_a_small_discount():
    assert truth_for(stats_for(3.0), UserProfile(), None).action == "callar"


def test_truth_is_silent_when_over_the_users_budget():
    truth = truth_for(stats_for(30.0, current=30000), UserProfile(max_price=25000), None)
    assert truth.is_real is True
    assert truth.fits_user is False
    assert truth.action == "callar"


def test_truth_ignores_the_advertised_list_price():
    stats = stats_for(0.0)
    assert truth_for(stats, UserProfile(), 90000) == truth_for(stats, UserProfile(), None)
