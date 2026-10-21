from datetime import date, timedelta

import pytest

from dealjudge.history import PricePoint, UserProfile, compute_stats, fits_profile, render_state

END = date(2026, 10, 20)


def make_series(prices):
    """prices[0] is the oldest day; the last one is END."""
    n = len(prices)
    return [PricePoint(END - timedelta(days=n - 1 - i), p) for i, p in enumerate(prices)]


def test_flat_series_has_no_discount_and_no_spike():
    stats = compute_stats(make_series([29990] * 90))
    assert stats.real_discount_pct == 0.0
    assert stats.spike_recent is False
    assert stats.baseline_median == 29990
    assert stats.days_of_history == 90


def test_inflated_spike_then_return_is_not_a_real_discount():
    stats = compute_stats(make_series([29990] * 60 + [39990] * 12 + [29990]))
    assert stats.spike_recent is True
    assert stats.spike_peak == 39990
    assert stats.baseline_median == 29990
    assert stats.real_discount_pct == 0.0


def test_real_drop_is_measured_against_the_median():
    stats = compute_stats(make_series([40000] * 85 + [32000]))
    assert stats.real_discount_pct == 20.0
    assert stats.current == 32000
    assert stats.min_price == 32000
    assert stats.days_since_last_drop == 0


def test_empty_series_is_rejected():
    with pytest.raises(ValueError):
        compute_stats([])


def test_single_point_does_not_crash():
    stats = compute_stats(make_series([15000]))
    assert stats.days_of_history == 1
    assert stats.real_discount_pct == 0.0


def test_zero_price_does_not_divide_by_zero():
    stats = compute_stats(make_series([0, 0, 0]))
    assert stats.real_discount_pct == 0.0


def test_render_state_has_the_figures_and_no_none():
    stats = compute_stats(make_series([40000] * 85 + [32000]))
    text = render_state("Aura X2 headphones", stats, None, UserProfile(max_price=35000))
    assert "current price: CLP 32,000" in text
    assert "90-day median: CLP 40,000" in text
    assert "price cap: CLP 35,000" in text
    assert "None" not in text


def test_fits_profile_checks_budget_and_minimum_level():
    stats = compute_stats(make_series([40000] * 85 + [32000]))  # 20 % below the median: "good"
    assert fits_profile(stats, UserProfile()) is True
    assert fits_profile(stats, UserProfile(max_price=35000, min_level="good")) is True
    assert fits_profile(stats, UserProfile(max_price=30000)) is False
    assert fits_profile(stats, UserProfile(min_level="very_good")) is False
