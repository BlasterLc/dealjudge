"""The three typed questions Decider answers about each offer, in one round trip."""

from typing import Any

LEVEL_CRITERIA = {
    "sin_oferta": "el precio actual está menos de 5 % bajo la mediana de 90 días",
    "marginal": "el precio actual está entre 5 % y 10 % bajo la mediana de 90 días",
    "buena": "el precio actual está entre 10 % y 25 % bajo la mediana de 90 días",
    "muy_buena": "el precio actual está entre 25 % y 40 % bajo la mediana de 90 días",
    "excepcional": "el precio actual está 40 % o más bajo la mediana de 90 días",
}


def decider_questions() -> dict[str, dict[str, Any]]:
    return {
        "is_real": {
            "type": "noul",
            "instructions": "¿Es real este descuento? Un descuento es real si el precio actual "
            "está al menos 10 % bajo la mediana de los 90 días anteriores a cualquier subida reciente.",
            "criteria": {
                "true": "el precio actual está al menos 10 % bajo esa mediana",
                "false": "no lo está, o el precio estuvo inflado poco antes de la oferta",
            },
        },
        "level": {
            "type": "choice",
            "instructions": "¿Qué nivel de oferta es, según el descuento real contra la mediana?",
            "criteria": dict(LEVEL_CRITERIA),
        },
        "fits_user": {
            "type": "noul",
            "instructions": "¿Esta oferta cumple lo que pide el usuario? Debe estar dentro de su "
            "tope de precio, si lo tiene, y alcanzar el nivel mínimo que pide.",
            "criteria": {
                "true": "el precio está dentro del tope y el nivel alcanza el mínimo pedido",
                "false": "el precio supera el tope o el nivel no alcanza el mínimo pedido",
            },
        },
    }
