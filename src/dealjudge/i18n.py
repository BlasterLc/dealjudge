"""Everything a person or a model reads, per language. The code itself uses English identifiers.

Two things are language-specific and easy to confuse:

- what a *person* sees (labels, alert text, reasons), and
- what *Decider* is shown and answers with: the state lines, the questions and the level names it
  picks from. These must be in one language end to end, so the model never reads a mixed prompt.
"""

from dealjudge.levels import LEVELS

LANGS = ("en", "es")
DEFAULT_LANG = "en"

# The level names Decider is shown and picks from, parallel to LEVELS.
LEVEL_KEYS = {
    "en": ("no_deal", "marginal", "good", "very_good", "exceptional"),
    "es": ("sin_oferta", "marginal", "buena", "muy_buena", "excepcional"),
}
LEVEL_LABELS = {
    "en": ("no deal", "marginal", "good", "very good", "exceptional"),
    "es": ("sin oferta", "marginal", "buena", "muy buena", "excepcional"),
}
ACTION_LABELS = {
    "en": {"alert": "Alert", "stay_silent": "Stay silent", "alert_with_warning": "Alert with caution"},
    "es": {"alert": "Avisar", "stay_silent": "Callar", "alert_with_warning": "Avisar con cautela"},
}

_PRODUCTS_ES = {
    "Wireless headphones": "Audífonos inalámbricos",
    "1TB SSD": "SSD 1TB",
    "Air fryer": "Freidora de aire",
    "Robot vacuum": "Aspiradora robot",
    "Mechanical keyboard": "Teclado mecánico",
    "Smartwatch": "Smartwatch",
    "Mid-range laptop": "Notebook gama media",
    "Running shoes": "Zapatillas running",
}

_TEXT = {
    "en": {
        "state_product": "Product: {product}",
        "state_current": "- current price: {value}",
        "state_median": "- 90-day median: {value}",
        "state_real_discount_label": "real discount vs the median",
        "state_real_discount": "- real discount vs the median: {pct}%",
        "state_min": "- lowest price: {value}",
        "state_days": "- days of history: {value}",
        "state_since_drop": "- days since the last drop: {value}",
        "state_no_drops": "no drops",
        "state_spike_yes": "- recent price spike: yes, up to {value}",
        "state_spike_no": "- recent price spike: no",
        "state_list_price": "- list price advertised by the store: {value}",
        "state_cap": "- user's price cap: {value}",
        "state_no_cap": "no cap",
        "state_min_level": "- minimum level the user asks for: {value}",
        "q_is_real": "Look at the line 'real discount vs the median'. Is it 10% or more?",
        "q_is_real_true": "that line shows 10% or more",
        "q_is_real_false": "that line shows less than 10%",
        "q_level": "What level of offer is it, according to the real discount vs the median?",
        "q_fits": "Does this offer meet what the user asks? It must be within their price cap, "
        "if they have one, and reach the minimum level they ask for.",
        "q_fits_true": "the price is within the cap and the level reaches the minimum asked",
        "q_fits_false": "the price is above the cap or the level is below the minimum asked",
        "reason_unreadable": "I could not read the model's answer reliably.",
        "reason_unknown_level": "I could not classify the offer level.",
        "reason_short_history": "There is little price history to judge.",
        "reason_low_confidence": "I am not sure about this verdict.",
        "reason_real_and_fits": "Real discount that meets what you ask.",
        "reason_not_real_or_no_fit": "It is not a real deal or it does not meet what you ask.",
        "deny_no_data": "There is no data for that offer.",
        "deny_repeat": "This offer was already announced at the same price.",
        "tool_no_verdict": "No verdict for that offer.",
        "not_alerted": "No alert sent. {reason}",
        "agent_system": "You are Dealjudge. For each offer you receive, call the send_alert tool with its "
        "offer_id, the product name and the current price. The tool may reject the alert: "
        "if it does, do not insist and do not make up another alert.",
        "notice_prompt": "Write an offer alert of 2 or 3 sentences in English, clear and without exaggeration.\n"
        "Use ONLY these figures, without inventing others:\n"
        "- product: {product}\n- current price: {price}\n- 90-day median: {median}\n"
        "- real discount vs the median: {pct}%\n- lowest price: {minimum}\n{warning}\n"
        "Reply with the text of the alert only.",
        "notice_warning": "- include a clear warning: {reason}",
        "notice_template": "{product}: now {price}, {pct}% below the 90-day median ({median}). "
        "Lowest recorded: {minimum}.",
        "notice_caution": " Be careful: {reason}",
        "llm_prompt": "You are an offer judge. You read a product's state and answer three questions.\n\n"
        "{state}\n\nQuestions:\n"
        "1. is_real (true/false): is this discount real? It is real if the current price is at least "
        "10% below the median of the 90 days before any recent spike.\n"
        "2. level: what level of offer is it? Pick one:\n{levels}\n"
        "3. fits_user (true/false): does it meet what the user asks? It must be within their price cap, "
        "if they have one, and reach the minimum level they ask for.\n\n"
        'Reply ONLY with a JSON object: {{"is_real": bool, "level": str, "fits_user": bool}}',
    },
    "es": {
        "state_product": "Producto: {product}",
        "state_current": "- precio actual: {value}",
        "state_median": "- mediana de 90 días: {value}",
        "state_real_discount_label": "descuento real contra la mediana",
        "state_real_discount": "- descuento real contra la mediana: {pct} %",
        "state_min": "- precio mínimo: {value}",
        "state_days": "- días de historial: {value}",
        "state_since_drop": "- días desde la última baja: {value}",
        "state_no_drops": "no hubo bajas",
        "state_spike_yes": "- pico reciente de precio: sí, hasta {value}",
        "state_spike_no": "- pico reciente de precio: no",
        "state_list_price": "- precio de lista anunciado por la tienda: {value}",
        "state_cap": "- tope del usuario: {value}",
        "state_no_cap": "sin tope",
        "state_min_level": "- nivel mínimo que pide el usuario: {value}",
        "q_is_real": "Mira la línea 'descuento real contra la mediana'. ¿Es de 10 % o más?",
        "q_is_real_true": "esa línea marca 10 % o más",
        "q_is_real_false": "esa línea marca menos de 10 %",
        "q_level": "¿Qué nivel de oferta es, según el descuento real contra la mediana?",
        "q_fits": "¿Esta oferta cumple lo que pide el usuario? Debe estar dentro de su tope de precio, "
        "si lo tiene, y alcanzar el nivel mínimo que pide.",
        "q_fits_true": "el precio está dentro del tope y el nivel alcanza el mínimo pedido",
        "q_fits_false": "el precio supera el tope o el nivel no alcanza el mínimo pedido",
        "reason_unreadable": "No pude leer con seguridad la respuesta del modelo.",
        "reason_unknown_level": "No pude clasificar el nivel de la oferta.",
        "reason_short_history": "Hay poco historial de precios para juzgar.",
        "reason_low_confidence": "No estoy seguro de este veredicto.",
        "reason_real_and_fits": "Descuento real que cumple lo que pides.",
        "reason_not_real_or_no_fit": "No es una oferta real o no cumple lo que pides.",
        "deny_no_data": "No hay datos de esa oferta.",
        "deny_repeat": "Ya se avisó de esta oferta al mismo precio.",
        "tool_no_verdict": "Sin veredicto para esa oferta.",
        "not_alerted": "No se avisó. {reason}",
        "agent_system": "Eres Dealjudge. Para cada oferta que recibas, llama a la herramienta send_alert con su "
        "offer_id, el nombre del producto y el precio actual. La herramienta puede rechazar el aviso: "
        "si lo rechaza, no insistas ni inventes otro aviso.",
        "notice_prompt": "Escribe un aviso de oferta de 2 o 3 frases en español, claro y sin exagerar.\n"
        "Usa SOLO estas cifras, sin inventar otras:\n"
        "- producto: {product}\n- precio actual: {price}\n- mediana de 90 días: {median}\n"
        "- descuento real contra la mediana: {pct} %\n- precio mínimo: {minimum}\n{warning}\n"
        "Responde solo con el texto del aviso.",
        "notice_warning": "- incluye una advertencia clara: {reason}",
        "notice_template": "{product}: ahora {price}, {pct} % bajo la mediana de 90 días ({median}). "
        "Mínimo registrado: {minimum}.",
        "notice_caution": " Ten cautela: {reason}",
        "llm_prompt": "Eres un juez de ofertas. Lees el estado de un producto y respondes tres preguntas.\n\n"
        "{state}\n\nPreguntas:\n"
        "1. is_real (true/false): ¿es real este descuento? Es real si el precio actual está al menos "
        "10 % bajo la mediana de los 90 días anteriores a cualquier subida reciente.\n"
        "2. level: ¿qué nivel de oferta es? Elige uno:\n{levels}\n"
        "3. fits_user (true/false): ¿cumple lo que pide el usuario? Debe estar dentro de su tope de precio, "
        "si lo tiene, y alcanzar el nivel mínimo que pide.\n\n"
        'Responde SOLO con un objeto JSON: {{"is_real": bool, "level": str, "fits_user": bool}}',
    },
}

_LEVEL_CRITERIA = {
    "en": (
        "the current price is less than 5% below the 90-day median",
        "the current price is between 5% and 10% below the 90-day median",
        "the current price is between 10% and 25% below the 90-day median",
        "the current price is between 25% and 40% below the 90-day median",
        "the current price is 40% or more below the 90-day median",
    ),
    "es": (
        "el precio actual está menos de 5 % bajo la mediana de 90 días",
        "el precio actual está entre 5 % y 10 % bajo la mediana de 90 días",
        "el precio actual está entre 10 % y 25 % bajo la mediana de 90 días",
        "el precio actual está entre 25 % y 40 % bajo la mediana de 90 días",
        "el precio actual está 40 % o más bajo la mediana de 90 días",
    ),
}


def _check(lang: str) -> str:
    if lang not in LANGS:
        raise ValueError(f"unknown language {lang!r}; use one of {LANGS}")
    return lang


def text(lang: str, name: str, **fields: object) -> str:
    return _TEXT[_check(lang)][name].format(**fields)


def money(lang: str, amount: int) -> str:
    """Chilean pesos, as each language writes them: $16.120 / CLP 16,120."""
    if _check(lang) == "es":
        return "$" + format(int(amount), ",").replace(",", ".")
    return "CLP " + format(int(amount), ",")


def level_key(lang: str, level: str) -> str:
    return LEVEL_KEYS[_check(lang)][LEVELS.index(level)]


def level_from_key(lang: str, key: str) -> str | None:
    keys = LEVEL_KEYS[_check(lang)]
    return LEVELS[keys.index(key)] if key in keys else None


def level_label(lang: str, level: str) -> str:
    return LEVEL_LABELS[_check(lang)][LEVELS.index(level)]


def action_label(lang: str, action: str) -> str:
    return ACTION_LABELS[_check(lang)][action]


def level_criteria(lang: str) -> dict[str, str]:
    """Model-facing level name -> what it means, in the language Decider reads."""
    return dict(zip(LEVEL_KEYS[_check(lang)], _LEVEL_CRITERIA[lang]))


def reason_text(lang: str, code: str) -> str:
    return text(lang, f"reason_{code}")


def product_name(lang: str, name: str) -> str:
    """The product name in ``lang``. Names that are not in the demo catalogue pass through."""
    return _PRODUCTS_ES.get(name, name) if _check(lang) == "es" else name
