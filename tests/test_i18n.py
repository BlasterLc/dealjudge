import pytest

from dealjudge import i18n
from dealjudge.history import PricePoint, UserProfile, compute_stats, render_state
from dealjudge.levels import LEVELS
from dealjudge.policy import REASONS
from dealjudge.questions import decider_questions
from datetime import date, timedelta

END = date(2026, 10, 20)
PRICES = [40000] * 85 + [32000]
STATS = compute_stats([PricePoint(END - timedelta(days=len(PRICES) - 1 - i), p) for i, p in enumerate(PRICES)])


@pytest.mark.parametrize("lang", i18n.LANGS)
def test_level_keys_round_trip_to_the_canonical_levels(lang):
    assert [i18n.level_from_key(lang, i18n.level_key(lang, lv)) for lv in LEVELS] == list(LEVELS)


def test_unknown_level_key_maps_to_none_and_wrong_language_does_not_match():
    assert i18n.level_from_key("en", "nonsense") is None
    assert i18n.level_from_key("en", "muy_buena") is None
    assert i18n.level_from_key("es", "very_good") is None


def test_unknown_language_is_refused():
    with pytest.raises(ValueError):
        i18n.money("fr", 1000)


def test_money_follows_the_local_convention():
    assert i18n.money("es", 16120) == "$16.120"
    assert i18n.money("en", 16120) == "CLP 16,120"


@pytest.mark.parametrize("lang", i18n.LANGS)
def test_every_reason_code_has_a_text(lang):
    for code in REASONS:
        assert i18n.reason_text(lang, code)


def test_product_names_are_translated_and_unknown_ones_pass_through():
    assert i18n.product_name("es", "Wireless headphones") == "Audífonos inalámbricos"
    assert i18n.product_name("en", "Wireless headphones") == "Wireless headphones"
    assert i18n.product_name("es", "Some real store title") == "Some real store title"


@pytest.mark.parametrize("lang", i18n.LANGS)
def test_state_is_in_one_language_and_has_no_none(lang):
    text = render_state("Product", STATS, None, UserProfile(max_price=35000), lang)
    assert "None" not in text and "nan" not in text
    assert i18n.money(lang, STATS.current) in text


def test_state_english_has_no_spanish_labels_and_spanish_has_no_english_ones():
    en = render_state("Product", STATS, None, UserProfile(), "en")
    es = render_state("Producto", STATS, None, UserProfile(), "es")
    assert "current price" in en and "precio actual" not in en
    assert "precio actual" in es and "current price" not in es
    assert "minimum level the user asks for: good" in en
    assert "nivel mínimo que pide el usuario: buena" in es


@pytest.mark.parametrize("lang", i18n.LANGS)
def test_the_question_points_at_a_line_that_the_state_really_has(lang):
    label = i18n.text(lang, "state_real_discount_label")
    assert label in render_state("P", STATS, None, UserProfile(), lang)
    assert label in decider_questions(lang)["is_real"]["instructions"]


@pytest.mark.parametrize("lang", i18n.LANGS)
def test_level_choices_use_the_model_facing_keys_of_that_language(lang):
    assert tuple(decider_questions(lang)["level"]["criteria"]) == i18n.LEVEL_KEYS[lang]
