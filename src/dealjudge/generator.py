"""Simulated offers with a known answer.

Each case is a 90-day price series built from a scenario. The truth of a case comes from
``truth_for`` over the series' own history figures, so it is reproducible and needs no
hand labelling. The generator is public on purpose: anyone can check what "real" means here.
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta

from dealjudge.history import HistoryStats, PricePoint, UserProfile, compute_stats, fits_profile
from dealjudge.levels import level_for

SCENARIOS = (
    "pico_inflado",
    "baja_genuina",
    "fluctuacion_normal",
    "oferta_recurrente",
    "historial_corto",
    "limite_10",
    "limite_25",
)

END_DAY = date(2026, 10, 20)
DAYS = 90
MIN_FULL_HISTORY = 14
NOISE = 0.02

# (name, low, high) base price in CLP, one per product the registrar watches
PRODUCTS = (
    ("Audifonos inalambricos", 15000, 60000),
    ("SSD 1TB", 55000, 120000),
    ("Freidora de aire", 35000, 90000),
    ("Aspiradora robot", 90000, 300000),
    ("Teclado mecanico", 25000, 80000),
    ("Smartwatch", 30000, 150000),
    ("Notebook gama media", 350000, 600000),
    ("Zapatillas running", 40000, 110000),
)


@dataclass(frozen=True)
class Truth:
    is_real: bool
    level: str
    fits_user: bool
    action: str


@dataclass(frozen=True)
class Case:
    id: str
    scenario: str
    product: str
    series: list[PricePoint]
    advertised_list_price: int | None
    profile: UserProfile
    truth: Truth


def truth_for(
    stats: HistoryStats, profile: UserProfile, advertised_list_price: int | None
) -> Truth:
    """The correct answer for a series. The advertised list price is ignored on purpose:
    a store's claimed discount says nothing about whether the discount is real."""
    is_real = stats.real_discount_pct >= 10.0
    level = level_for(stats.real_discount_pct)
    fits_user = fits_profile(stats, profile)
    if stats.days_of_history < MIN_FULL_HISTORY:
        action = "avisar_con_advertencia"
    elif is_real and fits_user:
        action = "avisar"
    else:
        action = "callar"
    return Truth(is_real, level, fits_user, action)


def _price(rng: random.Random, base: float) -> int:
    return int(round(base * (1 + rng.uniform(-NOISE, NOISE)), -1))


def _series(prices: list[int]) -> list[PricePoint]:
    n = len(prices)
    return [PricePoint(END_DAY - timedelta(days=n - 1 - i), p) for i, p in enumerate(prices)]


def _flat(rng: random.Random, base: float, n: int = DAYS) -> list[int]:
    return [_price(rng, base) for _ in range(n)]


def _pico_inflado(rng, base):
    prices = _flat(rng, base)
    length, end = rng.randint(8, 14), DAYS - 1 - rng.randint(1, 7)
    multiplier = rng.uniform(1.25, 1.40)
    for i in range(end - length + 1, end + 1):
        prices[i] = _price(rng, base * multiplier)
    return prices, int(round(base * rng.uniform(1.25, 1.5), -1))


def _baja_genuina(rng, base):
    prices = _flat(rng, base)
    drop = rng.uniform(0.15, 0.50)
    for i in range(DAYS - rng.randint(1, 5), DAYS):
        prices[i] = _price(rng, base * (1 - drop))
    return prices, None


def _fluctuacion_normal(rng, base):
    prices = _flat(rng, base)
    prices[-1] = _price(rng, base * (1 - rng.uniform(0.0, 0.09)))
    return prices, None


def _oferta_recurrente(rng, base):
    offset = rng.randrange(21)
    return [
        _price(rng, base * (0.85 if (i + offset) % 21 < 3 else 1.0)) for i in range(DAYS)
    ], None


def _historial_corto(rng, base):
    prices = _flat(rng, base, rng.randint(3, 10))
    prices[-1] = _price(rng, base * (1 - rng.uniform(0.15, 0.40)))
    return prices, None


def _limite(target_pct):
    def build(rng, base):
        prices = _flat(rng, base)
        baseline = compute_stats(_series(prices)).baseline_median
        goal = target_pct + rng.uniform(-0.3, 0.3)
        prices[-1] = int(round(baseline * (1 - goal / 100)))
        return prices, None

    return build


_BUILDERS = {
    "pico_inflado": _pico_inflado,
    "baja_genuina": _baja_genuina,
    "fluctuacion_normal": _fluctuacion_normal,
    "oferta_recurrente": _oferta_recurrente,
    "historial_corto": _historial_corto,
    "limite_10": _limite(10.0),
    "limite_25": _limite(25.0),
}


def _profile(rng: random.Random, current: int) -> UserProfile:
    max_price = None if rng.random() < 0.4 else int(round(current * rng.uniform(0.85, 1.3), -1))
    return UserProfile(max_price=max_price, min_level=rng.choice(("marginal", "buena", "buena", "muy_buena")))


def generate_cases(n_per_scenario: int, seed: int) -> list[Case]:
    cases = []
    for scenario in SCENARIOS:
        for i in range(n_per_scenario):
            rng = random.Random(f"{seed}-{scenario}-{i}")
            product, low, high = PRODUCTS[i % len(PRODUCTS)]
            base = rng.uniform(low, high)
            prices, advertised = _BUILDERS[scenario](rng, base)
            series = _series(prices)
            profile = _profile(rng, prices[-1])
            truth = truth_for(compute_stats(series), profile, advertised)
            cases.append(Case(f"{scenario}-{i:03d}", scenario, product, series, advertised, profile, truth))
    return cases
