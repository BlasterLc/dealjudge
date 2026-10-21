"""Offer levels, from the real discount against the baseline median."""

LEVELS = ("no_deal", "marginal", "good", "very_good", "exceptional")

# Lower bound (inclusive) of each level, in percent below the baseline median.
_LOWER_BOUNDS = (("exceptional", 40.0), ("very_good", 25.0), ("good", 10.0), ("marginal", 5.0))


def level_for(discount_pct: float) -> str:
    for level, lower in _LOWER_BOUNDS:
        if discount_pct >= lower:
            return level
    return "no_deal"
