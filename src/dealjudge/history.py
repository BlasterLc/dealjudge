"""Price history to the figures Decider is shown. All arithmetic lives here, not in the model."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from statistics import median

from dealjudge.i18n import DEFAULT_LANG, level_key, money, text
from dealjudge.levels import LEVELS, level_for

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
    min_level: str = "good"


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


def fits_profile(stats: HistoryStats, profile: UserProfile) -> bool:
    """Whether the offer is within the user's budget and reaches their minimum level.

    Computed in code, not by Decider: comparing a price with a cap and a level with a
    minimum is arithmetic, and the model answers it worse than chance (see the evaluation).
    """
    within_budget = profile.max_price is None or stats.current <= profile.max_price
    return within_budget and LEVELS.index(level_for(stats.real_discount_pct)) >= LEVELS.index(profile.min_level)


def render_state(
    product: str,
    stats: HistoryStats,
    advertised_list_price: int | None,
    profile: UserProfile,
    lang: str = DEFAULT_LANG,
) -> str:
    """The text Decider reads: one figure per line, all in ``lang``."""
    t = lambda name, **f: text(lang, name, **f)  # noqa: E731
    m = lambda amount: money(lang, amount)  # noqa: E731
    since_drop = t("state_no_drops") if stats.days_since_last_drop is None else stats.days_since_last_drop
    lines = [
        t("state_product", product=product),
        t("state_current", value=m(stats.current)),
        t("state_median", value=m(stats.baseline_median)),
        t("state_real_discount", pct=f"{stats.real_discount_pct:.1f}"),
        t("state_min", value=m(stats.min_price)),
        t("state_days", value=stats.days_of_history),
        t("state_since_drop", value=since_drop),
        t("state_spike_yes", value=m(stats.spike_peak)) if stats.spike_recent else t("state_spike_no"),
    ]
    if advertised_list_price:
        lines.append(t("state_list_price", value=m(advertised_list_price)))
    lines.append(t("state_cap", value=t("state_no_cap") if profile.max_price is None else m(profile.max_price)))
    lines.append(t("state_min_level", value=level_key(lang, profile.min_level)))
    return "\n".join(lines)
