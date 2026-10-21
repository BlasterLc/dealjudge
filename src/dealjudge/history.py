"""Price history to the figures Decider is shown. All arithmetic lives here, not in the model."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from statistics import median

SPIKE_FACTOR = 1.15
RECENT_DAYS = 30
WINDOW_DAYS = 90
MIN_REFERENCE_DAYS = 14


@dataclass(frozen=True)
class PricePoint:
    day: date
    price: int


@dataclass(frozen=True)
class UserProfile:
    max_price: int | None = None
    min_level: str = "buena"


@dataclass(frozen=True)
class HistoryStats:
    current: int
    baseline_median: int
    min_price: int
    days_of_history: int
    days_since_last_drop: int | None
    spike_recent: bool
    spike_peak: int | None
    real_discount_pct: float


def compute_stats(series: Sequence[PricePoint]) -> HistoryStats:
    """Stats as of the last point of ``series``.

    The reference is the median of prices older than 30 days (the whole series when
    there are fewer than 14 such points). A spike is a price in the last 30 days, today
    excluded, at least 1.15 times that reference. With a spike the baseline is the
    reference; without one it is the median of the last 90 days.
    """
    if not series:
        raise ValueError("empty price series")
    points = sorted(series, key=lambda p: p.day)
    today = points[-1].day
    current = points[-1].price
    age = lambda p: (today - p.day).days  # noqa: E731

    older = [p.price for p in points if age(p) > RECENT_DAYS]
    reference = median(older) if len(older) >= MIN_REFERENCE_DAYS else median(p.price for p in points)

    recent = [p.price for p in points if 0 < age(p) <= RECENT_DAYS]
    peak = max(recent) if recent else None
    spike = peak is not None and reference > 0 and peak >= SPIKE_FACTOR * reference

    window = [p.price for p in points if age(p) < WINDOW_DAYS]
    baseline = int(round(reference if spike else median(window)))
    discount = round(max(0.0, (baseline - current) / baseline * 100), 1) if baseline > 0 else 0.0

    since_drop = None
    for i in range(len(points) - 1, 0, -1):
        if points[i].price < points[i - 1].price:
            since_drop = age(points[i])
            break

    return HistoryStats(
        current=current,
        baseline_median=baseline,
        min_price=min(window),
        days_of_history=(today - points[0].day).days + 1,
        days_since_last_drop=since_drop,
        spike_recent=spike,
        spike_peak=peak if spike else None,
        real_discount_pct=discount,
    )


def _clp(n: int) -> str:
    return "$" + format(int(n), ",").replace(",", ".")


def render_state(
    product: str,
    stats: HistoryStats,
    advertised_list_price: int | None,
    profile: UserProfile,
) -> str:
    """The text Decider reads: one figure per line, in Spanish."""
    lines = [
        f"Producto: {product}",
        f"- precio actual: {_clp(stats.current)}",
        f"- mediana de 90 días: {_clp(stats.baseline_median)}",
        f"- descuento real contra la mediana: {stats.real_discount_pct:.1f} %",
        f"- precio mínimo: {_clp(stats.min_price)}",
        f"- días de historial: {stats.days_of_history}",
    ]
    if stats.days_since_last_drop is None:
        lines.append("- días desde la última baja: no hubo bajas")
    else:
        lines.append(f"- días desde la última baja: {stats.days_since_last_drop}")
    if stats.spike_recent:
        lines.append(f"- pico reciente de precio: sí, hasta {_clp(stats.spike_peak)}")
    else:
        lines.append("- pico reciente de precio: no")
    if advertised_list_price:
        lines.append(f"- precio de lista anunciado por la tienda: {_clp(advertised_list_price)}")
    if profile.max_price is None:
        lines.append("- tope del usuario: sin tope")
    else:
        lines.append(f"- tope del usuario: {_clp(profile.max_price)}")
    lines.append(f"- nivel mínimo que pide el usuario: {profile.min_level}")
    return "\n".join(lines)
