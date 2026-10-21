import pytest

from dealjudge.levels import LEVELS, level_for


@pytest.mark.parametrize(
    "pct, expected",
    [
        (-3.0, "sin_oferta"),
        (4.99, "sin_oferta"),
        (5.0, "marginal"),
        (9.99, "marginal"),
        (10.0, "buena"),
        (24.99, "buena"),
        (25.0, "muy_buena"),
        (39.99, "muy_buena"),
        (40.0, "excepcional"),
        (80.0, "excepcional"),
    ],
)
def test_level_boundaries(pct, expected):
    assert level_for(pct) == expected


def test_levels_are_ordered_from_worst_to_best():
    assert LEVELS == ("sin_oferta", "marginal", "buena", "muy_buena", "excepcional")
