# Guion del video, narración en español (menos de 3:00)

English version: [video-script.md](video-script.md). Graba un idioma por video; usa la página en el mismo idioma
y las cifras de `results/<idioma>/evaluation.json`. Este guion usa `results/es/`.

Narración en español, subtítulos en inglés (o al revés con el guion en inglés). Usa solo las tiendas ficticias que
muestra la página. Sin música, o con música cuya licencia lo permita. Pantalla: la página de Dealjudge a 1280 px,
en el mismo idioma que la narración. Graba las páginas de `web/` desde un servidor local. No muestres marcas de
terceros (la sección de trabajos relacionados del artículo no se filma).

| Tiempo | Pantalla | Narración |
|---|---|---|
| 0:00-0:20 | Una etiqueta de precio con un "-25 %" rojo enorme; corte a la página | "En cada Cyber hay descuentos que no lo son: el precio sube semanas antes y luego baja a donde siempre estuvo. Dealjudge juzga cada oferta contra 90 días de precios." |
| 0:20-0:55 | Abrir el producto con alza inflada: el veredicto "callar" y el panel "Cómo decidió Decider" (tres respuestas, seguridad frente al umbral). Abrir el gráfico plegado y acercar el pico rojo | "Aquí la tienda anuncia un gran descuento, pero el precio estuvo inflado: la mediana de 90 días es casi igual a hoy. Decider lee las cifras y responde con seguridad: no es real. Dealjudge calla, y explica por qué." |
| 0:55-1:25 | Abrir el producto con baja genuina (aviso), mostrar el texto del aviso | "Esta sí es una baja real, muy por debajo de la mediana. Solo aquí avisa, con las cifras que lo respaldan; Bedrock redacta el texto." |
| 1:25-1:50 | Abrir el producto con historial corto (aviso con advertencia) | "Cuando no está seguro, o hay poco historial, avisa igual pero con una advertencia visible. La duda no se esconde." |
| 1:50-2:30 | `results/es/evaluation.md`: la tabla y las líneas de calibración | "Lo medimos contra la regla de antes y contra un LLM grande, con ofertas simuladas y declaradas como tales. Decider acierta 92 % al decidir si avisar, contra 81 % de la regla anterior. El LLM de Bedrock llega a 94 %, y ahí Decider queda un poco por debajo; lo que da es una sola llamada local de unos 280 milisegundos, sin costo de API y sin fallas, con probabilidades que el código usa para avisar con advertencia cuando duda." |
| 2:30-2:45 | La figura `docs/img/how-it-works.es.png` (preguntas tipadas, regla en código) y luego `patterns/policy/policy_gate.py` y su README | "El patrón es reutilizable: preguntas tipadas, tu propia función decide, falla cerrado. Un solo archivo." |
| 2:45-2:55 | URL del repo y título del artículo | "Dealjudge, Apache-2.0. Código y artículo en el enlace." |

Revisar antes de publicar: enlace público, menos de 3:00, sin marcas de terceros visibles, sin música con derechos,
subtítulos activados, cada cifra coincide con `results/es/evaluation.json` (0,919, 0,814, 0,938) y la página
mostrada es la final.
