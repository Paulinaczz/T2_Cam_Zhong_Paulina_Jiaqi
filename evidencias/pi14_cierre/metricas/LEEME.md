# O8 · Viabilidad de extracción desde código fuente

**Resultado:** una demostración parcial desde C es reproducible. Ninguna herramienta quedó verificada como fuente equivalente de las 21 columnas para el E6 actual. El [mapeo de las 21 columnas](mapeo_21.csv) identifica candidatos, fórmulas a contrastar y las verificaciones que faltan. El contrato de la aplicación comprueba encabezados, tipos y límites; no identifica qué analizador produjo los valores.

## Herramientas y alcance comprobado

- **McCabe IQ** documenta complejidad ciclomática, esencial y de diseño por módulo, métricas Halstead y líneas mixtas. Es el candidato principal para evaluar equivalencia sobre C. Falta confirmar con una instalación qué identificadores, parámetros y granularidad exporta, y qué cuenta exactamente branchCount. Disponible según documentación del fabricante, sin ejecución local. [Glosario McCabe IQ](https://www.mccabe.com/iq_research_metrics.htm) · [Definiciones de grafos de NIST](https://doi.org/10.6028/NIST.SP.500-235)
- **SciTools Understand** documenta Cyclomatic, Essential, conteos de líneas y ocho métricas Halstead útiles (cuatro conteos, longitud, volumen, dificultad y esfuerzo). No se verificó un identificador nativo completo para iv(G), branchCount ni líneas mixtas equivalentes al contrato histórico. Los conteos de código y comentario pueden solaparse. [Catálogo](https://documentation.scitools.com/metrics-list) · [Métricas Halstead](https://docs.scitools.com/plugins/Solutions/.doc/manager_halstead.html)
- **Lizard 1.25.0** se ejecutó sobre el [ejemplo C](ejemplo.c). Devolvió dos funciones, cada una con CCN 2, NLOC 7 y 8, y 21 y 46 tokens respectivamente. Es útil para ilustrar conteo por función y complejidad. Su NLOC y CCN quedan con sus nombres propios. Su salida no contiene la matriz de 21 métricas. [Lanzador](demo_lizard.py) · [Salida real](lizard_salida.json) · [Documentación de Lizard](https://github.com/terryyin/lizard)
- **Radon** documenta Halstead, conteos y complejidad sobre el AST de Python. Puede ilustrar fórmulas, pero no analiza la muestra C ni demuestra equivalencia de semántica o granularidad. [Documentación de Radon](https://radon.readthedocs.io/en/latest/intro.html)

## Contraste empírico de definiciones

En los cinco CSV de esta tesis, se probaron identidades candidatas con tolerancia absoluta 0,005 y relativa 1 %, salvo la igualdad exacta de los conteos de líneas. En JM1, loc y lOCode solo coinciden exactamente en 46 de 13 204 filas. La regla 2*v(g)-1 coincide con branchCount en 12 448 filas. El candidato b=v/3000 coincide en 13 202 filas, frente a 3 780 con b=e^(2/3)/3000. Para i, v/d coincide en 11 728 de 11 729 filas comparables, mientras l*v coincide en 5 553 de 13 204, compatible con pérdida de precisión del nivel almacenado. Estas asociaciones ayudan a reconstruir convenciones, sin certificar el instrumento histórico. El número de filas del JM1 congelado del proyecto también difiere del catálogo público Tera-PROMISE y no se intercambiaron esas versiones. [Identidades por proyecto](identidades_historicas.csv) · [Lanzador](comparar_identidades.py) · [Ficha pública de JM1](https://openscience.us/repo/defect/mccabehalsted/jm1.html)

## Reproducción de la demostración parcial

En un entorno separado instalar lizard==1.25.0. Desde la raíz del repositorio:

    python evidencias/pi14_cierre/metricas/demo_lizard.py

Para una demostración completa, fijar compilador/preprocesado, versión y configuración del extractor, unidad módulo y política de tokens y redondeo. Preparar ejemplos manuales con comentarios mixtos, blancos, decisiones, invocaciones, cortocircuito y una rama no estructurada. Exportar los grafos y la tabla de métricas del candidato. Comparar campo a campo con pares código fuente–fila generados por el extractor de referencia o con casos cuya definición y salida hayan sido validadas por el asesor. Reportar discrepancias por columna y bloqueos de licencia o disponibilidad. Hasta contar con ese contraste, la salida de la demostración queda fuera de la inferencia E6. No se incorporó extracción a Streamlit.
