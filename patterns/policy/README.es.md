# `#policy`: una pregunta tipada decide si una herramienta se ejecuta

Un solo archivo, `policy_gate.py`. Necesita `strands-agents` y un servidor de Strands Decider 2B en marcha.
([English version](README.md))

## Qué hace

Antes de que se ejecute una herramienta vigilada, la compuerta le hace a Decider tus **preguntas tipadas**
sobre la situación, en una sola ida y vuelta, y pasa las respuestas a **tu propia función en Python**, que
devuelve `("proceed" | "deny" | "guide", mensaje)`. La compuerta lo traduce a `Proceed`, `Deny` o `Guide`
del SDK. El modelo mide; tu código decide.

Úsala cuando una llamada a una herramienta deba depender de un juicio que un modelo de 2B puede hacer a
partir de texto (¿es un descuento real?, ¿es urgente esta solicitud?, ¿es confiable esta entrada?) y quieras
que la regla final sea código auditable y no otro prompt.

## La pregunta tipada

Una pregunta es un dato, no un prompt que se afina en cada llamada:

```python
{"type": "choice",                       # "choice" (elige una etiqueta) o "noul" (sí/no)
 "instructions": "¿Qué nivel de oferta es?",
 "criteria": {"buena": "entre 10 y 25 % bajo la mediana", "muy_buena": "entre 25 y 40 % bajo la mediana"}}
```

`choice` responde `{"choice": etiqueta, "probabilities": {...}, "confidence": número}`;
`noul` responde `{"noul": P(verdadero)}`.

## Conexión

```python
from strands import Agent
from policy_gate import PolicyGate, DeciderHTTP

gate = PolicyGate(
    questions=QUESTIONS,
    render=lambda event: f"tool={event.tool_use['name']} input={event.tool_use['input']}",
    decide=my_rule,                 # respuestas -> ("proceed" | "deny" | "guide", mensaje)
    client=DeciderHTTP(),           # DECIDER_URL, por defecto http://127.0.0.1:8000
    tools={"send_alert"},           # None vigila todas las herramientas
)
agent = Agent(model=..., tools=[send_alert], interventions=[gate])
```

Si el servidor no responde, o `decide` lanza una excepción, la compuerta niega la llamada: lo que no se
pudo juzgar no se ejecuta.

## Lo que aprendimos a golpes (mídelo con tus datos)

- **Apunta la pregunta a la cifra.** Preguntar "¿es real este descuento?" acertó 53 % en nuestros datos
  (en español, división de desarrollo); preguntar "mira la línea `descuento real contra la mediana`: ¿es de
  10 % o más?" acertó 94 %. Pon los números en el texto de estado y dile al modelo qué línea leer.
- **No le pidas aritmética.** Una pregunta que exigía comparar un precio con un tope *y* un nivel con un
  mínimo se respondió bien menos veces que el azar (37-41 %). Calcula eso en código y deja a Decider la lectura.
- **`confidence` no es una probabilidad.** En las preguntas `choice` vive en una escala baja (una elección
  correcta con P=0,30 reportó 0,13). Ajusta tu umbral con una división de desarrollo, con una regla que solo
  dé una respuesta decisiva cuando acierta más de la mitad de las veces.
- **Un solo idioma de punta a punta.** El estado, las preguntas y los nombres de las opciones deben estar en el
  mismo idioma; no mezcles un estado en español con etiquetas en inglés.

Mira cómo lo usa Dealjudge en `src/dealjudge/handler.py` y `src/dealjudge/policy.py`.
