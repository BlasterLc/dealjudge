"""Offer levels, from the real discount against the baseline median."""

LEVELS = ("sin_oferta", "marginal", "buena", "muy_buena", "excepcional")

# Lower bound (inclusive) of each level, in percent below the baseline median.
_LOWER_BOUNDS = (("excepcional", 40.0), ("muy_buena", 25.0), ("buena", 10.0), ("marginal", 5.0))


def level_for(discount_pct: float) -> str:
    for level, lower in _LOWER_BOUNDS:
        if discount_pct >= lower:
            return level
    return "sin_oferta"
