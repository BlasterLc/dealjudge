# Dealjudge: un modelo de 2B que te dice cuándo un descuento es falso

*Etiquetas: #strands-decider-2b #policy*

*English version: [article.md](article.md)*

En cada Cyber, el mismo truco: un precio sube unas semanas antes del evento y luego "baja" hasta donde siempre
estuvo, con un porcentaje rojo enorme al lado. Quería un agente que vigile los productos que me importan y solo me
moleste cuando el descuento sea **real**, o que me diga con claridad cuando no está seguro.

[Video: enlace aquí] · [Repo: enlace aquí]

## La decisión que le entregué a Decider 2B

Para cada oferta, el código calcula el historial de precios (mediana de los 90 días previos a cualquier alza
reciente, mínimo, días desde la última baja, si hubo un alza) y le entrega a Strands Decider 2B un texto corto con
una cifra por línea. Decider responde preguntas tipadas sobre él: *¿el descuento real es de 10 % o más?* (sí/no) y
*¿qué nivel de oferta es?* (`no_deal`, `marginal`, `good`, `very_good`, `exceptional`).

Luego **decide Python puro** (`policy.py`): un descuento real y seguro que le sirve al usuario se avisa (`alert`);
un "no es real" seguro se queda en silencio (`stay_silent`); **todo lo incierto se avisa con una advertencia
visible** (`alert_with_warning`). Un `InterventionHandler` de Strands aplica eso antes de que corra la herramienta
`send_alert`, y Amazon Bedrock redacta el aviso a partir de cifras que entrega el código. El modelo nunca es la
compuerta.

![Cómo decide Dealjudge: el código calcula el historial, Decider responde tres preguntas tipadas, una regla en Python elige avisar, avisar con advertencia o callar, y Bedrock solo redacta el aviso](docs/img/how-it-works.es.png)

Todo lo que lee el modelo y ve el usuario existe en inglés y en español, un idioma por ejecución.

## La página: primero el veredicto, luego cómo decidió Decider

Dealjudge incluye además una página estática pequeña (tiendas y precios simulados). Abre con el veredicto y después
muestra *cómo decidió Decider*: sus tres respuestas tipadas, cada una con su seguridad frente al umbral, y la regla
en código que las convirtió en una acción. El gráfico de 90 días está como evidencia, plegado: lo importante es la
decisión, no el gráfico.

![La página de Dealjudge: el veredicto, luego las tres respuestas de Decider con su seguridad frente al umbral, y la regla en código](docs/img/page-desktop.es.png)

La página lee datos ya juzgados (`web/data/demo.<idioma>.json`, escritos por `scripts/build_demo.py` con el Decider
y Bedrock reales). Su búsqueda de "agregar producto" es un catálogo simulado pequeño, no una búsqueda en vivo.

## Qué medí

Todas las cifras de abajo son sobre ofertas **simuladas**: 7 escenarios, 30 casos cada uno, 210 casos de prueba
(semilla 303), con una corrida en inglés y otra en español. El umbral de confianza (0,1) se fijó en una partición
de desarrollo distinta (semilla 101), nunca con los casos de prueba.

| Métrica (partición de prueba) | Decider + regla, EN | Decider + regla, ES | Regla antigua `cyber-watch` | Claude Haiku 4.5, EN / ES |
|---|---|---|---|---|
| Acierto avisar vs callar | 0,943 | 0,919 | 0,814 | 0,938 / 0,938 |
| Acierto de la acción en 3 vías | 0,943 | 0,895 | 0,690 | 0,933 / 0,929 |
| Acierto real vs falso | 1,000 | 0,948 | n/a | 0,962 / 0,971 |
| Acierto del nivel de oferta | 0,790 | 0,743 | n/a | 0,919 / 0,948 |
| Llamadas fallidas | 0 | 0 | 0 | 8 / 6 |
| Costo de API | 0 (local) | 0 (local) | 0 | US$0,11 / US$0,12 la corrida |

Lo que dice esto, sin adornos:

- **Decider supera a la regla antigua por 13 puntos en inglés y 10 en español** (0,943 y 0,919 contra 0,814). Es
  claramente mejor donde la regla es ciega: bajas genuinas que ya duran unos días (1,00 contra 0,57 en inglés,
  porque la regla solo compara hoy con ayer) y ofertas cerca de la línea de 25 % (1,00 contra 0,77).
- **Frente a un LLM más grande es un empate en la decisión que importa, y una derrota en el nivel.** Haiku 4.5
  saca 0,938 en avisar vs callar, lo mismo que Decider dentro del ruido (n=210), y gana en acierto del nivel
  (0,92-0,95 contra 0,74-0,79). Decider es más débil en los niveles intermedios (`good` 0,70, `very_good` 0,52 en
  inglés) y en ofertas justo en la línea de 10 %, donde solo iguala a la regla antigua (0,60 en inglés, 0,67 en
  español; el LLM saca 0,83).
- **Lo que aporta Decider no es acierto bruto.** Devuelve probabilidades en una llamada local, sin costo de API y
  sin llamadas fallidas (el LLM falló 8 y 6 veces, que cuento como advertencias), y el código puede usarlas:
  Decider respondió con decisión en el 86 % de las ofertas en inglés (83 % en español) y acertó el 93 % (91 %) de
  las veces en esas; el resto se avisó con una advertencia en vez de una adivinanza.
- **La calibración es imperfecta.** En real/falso el error de calibración esperado es 0,13 (EN) y 0,17 (ES), sobre
  todo porque el modelo es subconfiado (acierta el 100 % de las veces con una confianza media de unos 0,87 en
  inglés). En el nivel de oferta es 0,37 y 0,35, por eso el umbral se ajusta con datos.
- **Latencia y costo: medidos por separado, con salvedades.** Un benchmark aparte (70 estados simulados, llamadas
  secuenciales, Decider y el LLM en fases separadas, solo en inglés) dio a Decider una mediana de 278 ms (p95 336 ms,
  0 fallas) en una RTX 4050 de portátil junto al script, y a Haiku 4.5 en Bedrock 940 ms medidos desde la misma
  máquina (574 ms según Bedrock) a unos US$ 0,53 por 1.000 decisiones, contra cero costo de API para Decider. No es
  el mismo montaje (GPU local contra una API remota, llamada desde Chile), así que la diferencia es en parte del
  modelo y en parte de la red. Además, Bedrock limitó la tasa de 52 de 70 llamadas secuenciales en esta cuenta (sin
  reintentos), probablemente la razón de que el LLM "fallara" 8 y 6 veces en la evaluación. Las líneas de latencia de
  la propia evaluación (484 ms EN, 744 ms ES) intercalan las llamadas de ambos modelos, lo que inflaba a Decider en
  mis pruebas (545 ms contra 278 ms), así que cito el benchmark.

Las ofertas son **simuladas**: un generador público construye series de 90 días y la respuesta correcta sale de
las cifras de la propia serie. Eso hace que el benchmark trate de qué tan bien un modelo de 2B lee cifras, no de
tiendas reales. La regla antigua de `cyber-watch` (avisar ante una baja de 20 % respecto del último precio) es una
línea base independiente. También registro precios reales de tres sitios de retail chilenos cada seis horas, pero
no tienen verdad de referencia, así que no forman parte del benchmark.

## Cinco cosas que me sorprendieron

1. **La redacción movió el acierto de 53 % a 94 %.** En la partición de desarrollo, "¿Es real este descuento?" era
   casi una moneda al aire. "Mira la línea *descuento real vs mediana*: ¿es de 10 % o más?" funcionó. Señálale al
   modelo la cifra.
2. **Decider respondió peor que el azar en una comparación de dos partes.** "¿Le sirve al usuario?" (precio contra
   un tope *y* nivel contra un mínimo) sacó 37-41 % en desarrollo y 44 % (EN) / 41 % (ES) en la partición de
   prueba. Moví esa comparación al código, conservé la respuesta del modelo y la reporté. Coincide con la propia
   advertencia de la ficha del modelo sobre tareas más difíciles.
3. **`confidence` no es una probabilidad.** Para el nivel de oferta vive en una escala baja (una elección correcta
   con P=0,30 reportó 0,13), así que un umbral fijo de 0,70 hacía que todo advirtiera. Ajusté el umbral en una
   partición de desarrollo con una regla que solo da una respuesta decisiva cuando acierta más de la mitad de las veces.
4. **Lee mejor en inglés que en español.** Mismas ofertas, mismas preguntas traducidas: real/falso 1,00 contra
   0,95, nivel 0,79 contra 0,74, aviso 0,943 contra 0,919. La brecha apareció en la misma dirección en la semilla de
   desarrollo, y el LLM de Bedrock no la tuvo. Si tus usuarios escriben en otro idioma, prueba el modelo en ese idioma.
5. **El hardware importa más de lo que parece.** Unos 300 ms por llamada (tres preguntas) en una GPU de portátil;
   unos 12 s en CPU. Al desenchufar el cargador, la GPU desapareció de WSL y el servidor volvió a CPU en silencio.

## Trabajos relacionados

Los seguidores de precios como Knasta, SoloTodo, Keepa y CamelCamelCamel grafican el historial y avisan por un
umbral; no dicen si un descuento es real. Las extensiones de navegador (por ejemplo Fake Discount BG, SmartPrice
Guard y DealFury) marcan con reglas los precios "antes" inflados, y un actor de Apify, Deal Quality Scorer,
devuelve un puntaje, una bandera `alertWorthy` y una `confidence` a partir de la mediana histórica, que es lo más
parecido a la forma de salida de Dealjudge. Un consejo de Black Friday de una empresa de seguridad es pegar el
historial en un LLM y preguntarle; esa es la línea base contra la que mido. No encontré cifras de acierto
publicadas para ninguna de estas herramientas y no las he probado: esto sale de sus fichas públicas. Lo que añade
Dealjudge es una comparación medida, un veredicto que depende del tope y el mínimo del propio usuario, una política
que advierte en vez de adivinar y el patrón publicado como un archivo reutilizable.

## El patrón reutilizable: `#policy`

`patterns/policy/policy_gate.py` es un solo archivo: le das preguntas tipadas, una función que presenta la
situación como texto y tu propio `decide(answers)`; traduce el resultado a `Proceed`, `Deny` o `Guide`, y falla
cerrado si el servidor no responde. El cableado y las lecciones están en su README (inglés y español).

## Límites

Benchmark simulado; los precios reales no tienen verdad de referencia (el estado propio de Knasta se guarda solo
como referencia); los historiales de menos de 14 días siempre advierten por regla; hacer scraping de sitios de
retail es una zona gris; no están construidos el aviso por correo, agregar productos por mensaje ni Decider en
SageMaker.

## Pruébalo

`uv venv && uv pip install -e ".[dev]"`, inicia `strands-decider serve`, luego
`scripts/run_evaluation.py --lang es`, `scripts/bench_latency_cost.py` para la tabla de latencia y costo, y
`python -m http.server -d web` para la página. Todo es Apache-2.0.
