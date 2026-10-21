import pytest

from dealjudge.levels import LEVELS, level_for


@pytest.mark.parametrize(
    "pct, expected",
    [
        (-3.0, "no_deal"),
        (4.99, "no_deal"),
        (5.0, "marginal"),
        (9.99, "marginal"),
        (10.0, "good"),
        (24.99, "good"),
        (25.0, "very_good"),
        (39.99, "very_good"),
        (40.0, "exceptional"),
        (80.0, "exceptional"),
    ],
)
def test_level_boundaries(pct, expected):
    assert level_for(pct) == expected


def test_levels_are_ordered_from_worst_to_best():
    assert LEVELS == ("no_deal", "marginal", "good", "very_good", "exceptional")
