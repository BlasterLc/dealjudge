# Video script (under 3:00)

Narration in Spanish, English subtitles. Use only the fictional stores shown in the page. No music, or music with a
license that allows it. Screen: the Dealjudge page at 1280 px. Record the pages in `web/` from a local server.

| Time | Screen | Narration |
|---|---|---|
| 0:00-0:20 | A price tag with a big red "-25 %"; cut to the page | "En cada Cyber hay descuentos que no lo son: el precio sube semanas antes y luego baja a donde siempre estuvo. Dealjudge juzga cada oferta contra 90 días de precios." |
| 0:20-0:55 | Click the first ticket (inflated spike). Zoom the red spike on the chart, then the stamp NO AVISAR | "Aquí la tienda anuncia 50 mil, pero el precio estuvo inflado: la mediana de 90 días es casi igual a hoy. Decider lo lee y responde con seguridad: no es real. Dealjudge calla, y explica por qué." |
| 0:55-1:25 | Click the genuine drop (AVISAR), show "Lo que recibirías" | "Esta sí es una baja real, muy por debajo de la mediana. Solo aquí avisa, con las cifras que lo respaldan; Bedrock redacta el texto." |
| 1:25-1:50 | Click the short-history case (AVISAR CON CAUTELA) | "Cuando no está seguro, o hay poco historial, avisa igual pero con una advertencia visible. La duda no se esconde." |
| 1:50-2:30 | `results/evaluation.md`: the table and the calibration lines | "Lo medimos contra la regla de antes y contra un LLM, con ofertas simuladas y declaradas como tales. Decider acierta 90 % al decidir si avisar, contra 75 % de la regla anterior. Un LLM grande de Bedrock llega a 95 %, y ahí Decider pierde; lo que da es una sola llamada local, sin costo y sin fallas, con probabilidades que el código usa para avisar con advertencia cuando duda." |
| 2:30-2:50 | `patterns/policy/policy_gate.py` and its README | "El patrón es reutilizable: preguntas tipadas, tu propia función decide, falla cerrado. Un solo archivo." |
| 2:50-3:00 | Repo URL and article title | "Dealjudge, Apache-2.0. Código y artículo en el enlace." |

Check before publishing: public link, under 3:00, no third-party brands visible, no copyrighted music, English subtitles on.
