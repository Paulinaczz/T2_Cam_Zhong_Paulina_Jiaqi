# Escalabilidad, cohortes y alcance de OE4

## Capacidad operativa y tiempos

La validación impone 20 000 módulos y 10 MiB por CSV (10 485 760 bytes). Verifiqué la lectura de 20 000 filas sintéticas y el rechazo de 20 001 y de un archivo por encima del máximo de bytes. Esta comprobación cubre el lector, sin cronometrar inferencia en el límite.

El ensayo CP06 de O1 usó JM1 completo de 13 204 módulos, el 66,02 % del máximo por filas. Sus 30 mediciones dieron p95 de 47,783318 s para el flujo comparativo y 47,193291 s para inferencia. El lote de 18 obtuvo 0,096739 s de p95 comparativo. El protocolo original fijaba ≤5 s para 18 módulos sin arranque y 10 repeticiones. O6 pidió ≥30 repeticiones, un lote realista y validación e inferencia separadas. El resultado de JM1 es descriptivo: el plan no fija un umbral para ese tamaño ni valida tiempos a 20 000 módulos. Las cifras comparativas excluyen arranque, persistencia, inferencia adicional en UI04 y renderizado.

La recomendación nueva, sujeta a aprobación, es caracterizar lotes intermedios y el límite en un equipo fijo, medir memoria máxima y registrar tiempos extremo a extremo en UI04 por separado. Fijar cualquier objetivo de tiempo antes de contrastarlo. [Límites comprobados](comprobacion_limites.json) · [CP06 de O1](../../pi13/o1_20261115_181721/CP06_resumen_segundos.csv)

## Datos y esfuerzo de QA

- Corpus original, 17 442 registros de cinco proyectos NASA/PROMISE. La procedencia se documenta con URL y SHA-256. La identidad criptográfica de los archivos no certifica su curación documental.
- Cohorte principal, 11 690 vectores. Deduplicación global por 21 métricas antes de particionar. Se conserva una ocurrencia por vector; el propietario y la elección de ocurrencia se determinan sin la etiqueta.
- Sensibilidad, 11 569 vectores. Se excluyen los 121 grupos de X con etiquetas contradictorias antes de deduplicar. Usa etiquetas del corpus como limpieza del benchmark y se interpreta como análisis secundario. El flujo operativo recibe 21 métricas ya calculadas y carece de extracción automática y de etiquetas para reproducir esa exclusión en un proyecto nuevo.
- El presupuesto utiliza coste max(LOC, 1) y cuenta módulos completos bajo el mismo presupuesto. LOC aproxima tamaño. Complejidad, dependencia, contexto, experiencia, herramientas y trabajo de preparación afectan el tiempo real. Los resultados por LOC o módulos no permiten cuantificar minutos ahorrados ni defectos confirmados.

[Auditoría de cohortes](../../../research/auditoria/resumen_cohortes.json) · [Procedencia y huellas](../../../research/auditoria/fuentes_y_sha256.csv)

## OE4 e hipótesis

El plan evalúa rendimiento predictivo descriptivo (F1, AUC-ROC y AP externos) y priorización frente a ManualUp a igual presupuesto. La hipótesis de mejora operativa se concreta para la comparación por esfuerzo mediante Δ = Recall@20%LOC(estrategia ML) − Recall@20%LOC(ManualUp). Un Δ medio positivo expresa ventaja promedio en la muestra. La consistencia exige examinar signos por proyecto e incertidumbre.

El plan original incluía Wilcoxon bilateral y α=0,05. Su hipótesis nula de diferencia pareada centrada en cero se evalúa al nivel de proyecto. Con cinco pares sin ceros, el mínimo exacto bilateral bajo los supuestos de la prueba es 2/2⁵ = 0,0625. O2 pide retirar ese criterio de decisión, mostrar diferencias, mediana y proyectos favorables, y considerar intervalos bootstrap. El plan exploratorio de la estrategia calibrada se formuló tras conocer resultados del mismo corpus. Sus intervalos por proyecto condicionan en modelos entrenados y no cuantifican variación para proyectos nuevos. El criterio descriptivo documentado exige cinco deltas positivos y, como apoyo adicional, límites inferiores positivos. No se cumple: dos positivos, tres negativos y los cinco intervalos incluyen cero. No hay evidencia de superioridad consistente ni de equivalencia demostrada.

El CSV experimental identifica CM1 y JM1 como los dos deltas positivos. UI04 mostraba CM1 y PC1. Se corrigió el rótulo y se añadió una prueba que compara el texto renderizado con el CSV. Las cifras y las capturas históricas de O1 conservan su versión original. [Corrección y prueba](../UI04/LEEME.md)

[Plan exploratorio](../../../research/experimentos/estrategia_esfuerzo/plan_analisis_estrategia_esfuerzo.json) · [Deltas e intervalos archivados](../../../research/experimentos/estrategia_esfuerzo/principal_deduplicada/diferencias_20pct_LOC_por_proyecto.csv)
