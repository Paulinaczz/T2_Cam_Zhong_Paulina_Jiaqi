# Criterios científicos, metodología y límites del prototipo PDS-QA

Este documento resume los fundamentos metodológicos, la evidencia experimental obtenida y las limitaciones técnicas del modelo integrado en el prototipo de tesis (UNMSM).

---

## 1. Marco de investigación y evaluación

- **Design Science Research (DSR):** Marco rector para el diseño, desarrollo y validación iterativa del artefacto software.
- **CRISP-DM:** Guía metodológica para el ciclo de Machine Learning (comprensión del problema, análisis de datos, preprocesamiento, modelado, evaluación y despliegue).
- **Cross-Project Defect Prediction (CPDP):** Escenario de evaluación entre proyectos independientes. Se utilizaron 5 proyectos del repositorio NASA/PROMISE (`CM1`, `JM1`, `KC1`, `KC2`, `PC1`), sometidos a una deduplicación global previa a las particiones (11 690 instancias únicas).
- **Validación anidada (Nested Leave-One-Project-Out):** En cada uno de los 5 pliegues, un proyecto completo se reservó para prueba externa. La selección interna de hiperparámetros y transformaciones se realizó únicamente con los otros 4 proyectos, sin observar las etiquetas del proyecto objetivo.

---

## 2. Selección del modelo y evidencia experimental

### A. Selección histórica de la receta (`E6_ADASYN_MI`)
- **Pipeline seleccionado:** Clasificador Support Vector Machine (`SVM`) con sobremuestreo adaptativo `ADASYN` y selección de características por Información Mutua (`SelectKBest` con `mutual_info_classif`).
- **Criterio de selección:** Promedio no ponderado del F1 de la clase defectuosa entre proyectos.
- **Comparación directa E6 frente a E7:**
  - **`E6_ADASYN_MI`:** Macro F1 promedio = **0,4191** (AP: 0,3604; AUC: 0,7269; Recall: 0,6046).
  - **`E7_SMOTE_RF`:** Macro F1 promedio = **0,4146** (AP: 0,3628; AUC: 0,7260; Recall: 0,5508).
- **Prueba estadística pareada (Wilcoxon signed-rank):**
  - Estadístico \(W = 4,0\), \(p\)-valor bilateral exacto = **0,4375**.
  - **Interpretación:** No se detectó una diferencia estadísticamente significativa entre ambas recetas. Con una muestra de solo 5 proyectos, **la ausencia de significancia estadística no demuestra equivalencia**, reflejando que la ventaja observada es estrecha y dependiente del conjunto de datos.

### B. Resultados oficiales nuevos de OE3

| Algoritmo | F1 macro | AUC-ROC macro | AP macro |
|---|---:|---:|---:|
| XGBoost | 0,423066 | 0,711975 | 0,380567 |
| SVM | 0,413096 | 0,727687 | 0,348831 |
| Random Forest | 0,361601 | 0,693271 | 0,360133 |

XGBoost obtuvo el mayor F1 y AP del procedimiento Nested LOPO; SVM obtuvo el mayor AUC-ROC. E6 permanece como modelo operativo previamente validado. Esta decisión conserva el alcance funcional y las evidencias del prototipo; la integración de otro clasificador requeriría su validación operativa. El nuevo experimento no justifica superioridad estadística universal de E6.

En PI15 se completaron las 27 configuraciones y 675 ajustes candidatos de la búsqueda anidada y global. Los resultados se presentan como promedios de cinco proyectos externos con igual peso. [Entorno y resultados](../evidencias/pi15/oe3/RESULTADOS_OE3.md)

### C. Desempeño histórico en Colab
- En la evaluación histórica de Colab (*outer loop*), SVM superó a los algoritmos competidores en F1 y Recall:
  - **SVM:** Macro F1 outer = **0,4122** | AUC = **0,7277** | Recall = **0,5763**
  - **XGBoost:** Macro F1 outer = **0,3983** | AUC = **0,7123** | Recall = **0,4560**
  - **Random Forest:** Macro F1 outer = **0,3606** | AUC = **0,6899** | Recall = **0,4147**
- **Distinción metodológica fundamental:** La métrica de validación anidada (F1 = 0,4122) mide la capacidad de generalización del *procedimiento de modelado*. Es formalmente diferente de una prueba independiente sobre un hipotético sexto proyecto del artefacto serializado final (`modelo_predictivo_pds.joblib`), el cual fue reajustado con los 5 proyectos para su uso operativo.

---

## 3. Evaluación de priorización y esfuerzo de QA: Comparaciones experimentales

Se evaluó la eficacia de priorización bajo dos métricas de presupuesto: porcentaje de módulos inspeccionados y porcentaje de líneas de código (LOC). Es fundamental distinguir las tres evaluaciones realizadas:

### A. Experimento original: Procedimiento de selección anidada (Nested LOPO)
En la evaluación externa del pipeline seleccionado dinámicamente (`research/experimentos/QA_promedios_proyecto.csv`), los promedios al 20 % de presupuesto fueron:

| Estrategia (Nested LOPO) | Recall@20% Módulos | Recall@20% LOC (módulos completos) | Popt (0–20%) |
| :--- | :---: | :---: | :---: |
| **ManualUp (ordenar por LOC ascendente)** | 6,24 % | **28,74 %** | **0,2571** |
| **ML puro (procedimiento de selección)** | **42,39 %** | **18,02 %** | **0,1519** |
| **LOC descendente (módulos más grandes)** | 44,20 % | 9,40 % | 0,0607 |
| **Referencia aleatoria esperada** | 20,12 % | 19,87 % | 0,1698 |

*Resultado:* Al medir el esfuerzo en líneas de código, la regla determinista **ManualUp (28,74 %)** superó al **ML puro (18,02 %)**.

### B. Experimento exploratorio: Ranking híbrido lineal
En el análisis post-hoc exploratorio sobre la cohorte deduplicada completa (`research/experimentos/ranking_consciente_del_esfuerzo/comparacion_promedio.csv`):

| Estrategia | Recall@20% Módulos | Recall@20% LOC | Popt (0–20%) |
| :--- | :---: | :---: | :---: |
| **ManualUp (LOC ascendente puro)** | 6,24 % | **28,74 %** | **0,2571** |
| **Ranking Híbrido (peso óptimo ML)** | 6,47 % | **25,13 %** | **0,2186** |
| **SVM solo (sin combinar con LOC)** | **42,61 %** | **16,85 %** | **0,1460** |

### C. Nueva estrategia solicitada por el asesor: Probabilidad Calibrada / LOC
Para abordar rigurosamente la relación entre probabilidad de defecto y esfuerzo sin recurrir a ponderaciones heurísticas arbitrarias, se implementó la calibración de probabilidad mediante regresión sigmoide (Platt scaling) entrenada **exclusivamente con los proyectos fuente** (*out-of-fold*, sin fuga de información del proyecto objetivo). La prioridad se definió como:

$$\text{Prioridad}_i = \frac{\widehat{P}(\text{defecto}_i)}{\text{LOC}_i}$$

Los resultados consolidados en `research/experimentos/estrategia_esfuerzo/principal_deduplicada/` muestran:

| Métrica / Parámetro | E6 Calibrado / LOC | Heurística ManualUp | Diferencia ($\Delta$) | Interpretación |
| :--- | :--- | :--- | :--- | :--- |
| **Recall@20 % LOC (Promedio)** | **29,09 %** | **28,74 %** | **+0,36 p.p.** | Ventaja promedio marginal (+0,00356) |
| **Recall@10 % LOC (Promedio)** | 15,39 % | 15,25 % | +0,15 p.p. | Comportamiento prácticamente idéntico |
| **$P_{\text{opt}}$ normalizado (0–20 %)** | 25,50 % | 25,71 % | -0,21 p.p. | ManualUp ligeramente superior en área |
| **$P_{\text{opt}}$ normalizado (0–100 %)** | 62,39 % | 62,27 % | +0,12 p.p. | Empate global |
| **Proyectos con $\Delta > 0$ (favorece ML)** | 2 de 5 (CM1: +4,35 p.p., JM1: +0,85 p.p.) | — | — | ML gana en 2 proyectos |
| **Proyectos con $\Delta < 0$ (favorece ManualUp)** | — | 3 de 5 (KC1: -0,97 p.p., KC2: -1,02 p.p., PC1: -1,43 p.p.) | — | ManualUp gana en 3 proyectos |

#### Intervalos de Confianza Bootstrap al 95 % (1000 iteraciones)
- **CM1:** $\Delta = +4,35\text{ p.p.}$, IC 95 %: $[-5,56\text{ p.p.},\; +11,63\text{ p.p.}]$ (incluye 0)
- **JM1:** $\Delta = +0,85\text{ p.p.}$, IC 95 %: $[-0,83\text{ p.p.},\; +2,30\text{ p.p.}]$ (incluye 0)
- **KC1:** $\Delta = -0,97\text{ p.p.}$, IC 95 %: $[-3,04\text{ p.p.},\; +1,06\text{ p.p.}]$ (incluye 0)
- **KC2:** $\Delta = -1,02\text{ p.p.}$, IC 95 %: $[-7,22\text{ p.p.},\; +1,92\text{ p.p.}]$ (incluye 0)
- **PC1:** $\Delta = -1,43\text{ p.p.}$, IC 95 %: $[-4,29\text{ p.p.},\; +3,80\text{ p.p.}]$ (incluye 0)

### Conclusión Científica Unificada sobre Esfuerzo de QA
1. **Ausencia de superioridad consistente:** Dado que los intervalos bootstrap de las diferencias incluyen el cero en los 5 proyectos y el clasificador solo supera a ManualUp en 2 de los 5 casos, **no existe evidencia estadística suficiente para sostener superioridad consistente del modelo predictivo frente a la heurística de módulos pequeños (ManualUp)** cuando el esfuerzo se mide en líneas de código.
2. **Separación de propósitos:** Este resultado experimental corresponde a la investigación científica de esfuerzo en Colab y no debe confundirse con la aplicación operativa Streamlit, la cual ordena módulos por el margen del SVM `E6_ADASYN_MI`.

### D. Integración en el Prototipo Operativo (Atención a la Observación O1)
En respuesta a la observación O1 del asesor, se integró en la aplicación web la comparación interactiva entre las tres estrategias de priorización:
1. **Estrategia Operativa (Margen SVM E6):** Ordenamiento por margen de decisión descendente, preservando el comportamiento original del artefacto validado.
2. **Estrategia Experimental (Probabilidad Calibrada / LOC):** Modela la densidad de riesgo dividiendo la probabilidad estimada mediante calibración Platt $\widehat{P}(\text{defecto})$ entre las líneas de código $\text{LOC}$.
3. **Estrategia de Referencia (ManualUp):** Ordenamiento por $\text{LOC}$ ascendente (módulos más pequeños primero).

**Detalles de implementación y trazabilidad:**
- **Calibrador serializado:** `artifacts/models/calibrador_probabilidad_e6.joblib` (SHA-256: `a15aab94b20b2826f0ffd07e13a23bd36600743d26ec8657196b3f16f6884d19`), acompañado de `metadatos_calibrador.json` e `integridad_calibrador.json`.
- **Ajuste del calibrador:** En el experimento científico (Nested LOPO), cada pliegue ajustó su calibración exclusivamente con los 4 proyectos fuente. Para la inferencia en producción con el artefacto reentrenado en los 5 proyectos, se entrenó un calibrador logístico sobre las 11 690 predicciones históricas fuera de pliegue (*out-of-fold*) documentadas en `research/experimentos/estrategia_esfuerzo/principal_deduplicada/predicciones_por_proyecto.csv` ($\beta_1 = 0,7743$, $\beta_0 = -1,2852$).
- **Integridad del pipeline E6:** El archivo del pipeline original `modelo_predictivo_pds.joblib` (SHA-256: `5a420bc5...`) no sufrió ninguna alteración ni sustitución silenciosa.
- **Visualización en UI04:** La interfaz organiza la vista de resultados en dos pestañas claramente diferenciadas: una para el ranking operativo con margen SVM y otra para la matriz comparativa de estrategias, advirtiendo explícitamente que el ML no demostró superioridad consistente sobre ManualUp.

---

## 4. Evidencias de Validación Técnica y Operativa (PI13–PI14)

Las pruebas locales reproducibles registraron los siguientes resultados en `evidencias/pi13/validacion_local/`:

- **Casos funcionales y de seguridad:**
  - **CP01 (Importación y ranking 18 módulos):** Aprobado en backend y validado en UI.
  - **CP02 (Rechazo sin columna `loc`):** Aprobado en backend (`rechazo.txt`).
  - **CP03 (Rechazo de Inf y no numéricos):** Aprobado en backend (`rechazos.txt`).
  - **CP04 (Protección contra inyección de fórmulas CSV):** Aprobado en backend (`salida_sanitizada.csv`), comprobando que `=1+2` se escapa como `'=1+2`.
  - **CP05 (Historial e integridad SQLite):** Aprobado en backend y visualmente (`historial.csv`, `predicciones_sqlite.csv`).
  - **CP11 (Rechazo de formato no CSV y duplicados):** Aprobado en backend (`rechazos.txt`).
  - **CP12 (Bloqueo por alteración SHA-256):** Aprobado en backend sobre copia temporal (`rechazo_hash.txt`).
  - **Suite pytest de O1:** 15 pruebas aprobadas en la rama del PR #3. [Registro](../evidencias/pi13/o1_20261115_181721/suite_pytest.txt)

La [verificación operativa de O1](../evidencias/pi13/o1_20261115_181721/LEEME.md) comprobó la integridad de E6 y del calibrador serializado, los tres rankings y la exportación para 18 módulos (CP01), y la persistencia del UUID, las huellas y las 18 predicciones (CP05). En el prototipo, el ranking operativo sigue ordenado por margen E6. El calibrador ajustado sobre márgenes históricos fuera de pliegue se usa en la comparación de estrategias. El Nested LOPO de la sección anterior utiliza una calibración por pliegue y es la fuente de los resultados científicos frente a ManualUp. Esa evaluación no aporta evidencia de una mejora consistente.

**CP06 en el PR #3.** Se realizaron 30 repeticiones independientes por tamaño de lote, con un p95 del flujo comparativo de **0,096739 s** para 18 módulos y **47,783318 s** para JM1 completo (13 204 módulos). La meta original de 5 s aplica al lote pequeño. La inferencia en JM1 alcanzó un p95 de 47,193291 s. Se midieron por separado validación, inferencia, calibración, rankings y exportación. El total excluye arranque, persistencia, inferencia adicional en UI04 y renderizado. [Mediciones individuales](../evidencias/pi13/o1_20261115_181721/CP06_mediciones.csv) · [Resumen estadístico](../evidencias/pi13/o1_20261115_181721/CP06_resumen_segundos.csv)


---

## 5. Seguimiento PI13–PI14

- **UI04 corregida.** CM1 y JM1 son los proyectos con delta positivo en Recall@20 % LOC. La prueba de regresión obtiene los proyectos del CSV experimental y los compara con lo mostrado. Los resultados históricos conservan sus cifras. [Verificación](../evidencias/pi14_revision/UI04/LEEME.md)
- **CP09 — parcialmente comprobado.** Dos repeticiones locales con semilla 42 dieron CSV idénticos. Con NumPy 2.1.3 coincidieron las tres métricas históricas de 4 de 15 recetas, frente a 3 de 15 con la versión base. Cambiar el paquete NumPy y su OpenBLAS incluido produjo la primera diferencia local en el escalado. Cambiar el backend de distancias o el orden de empates afectó la vecindad y el balanceo ADASYN. No se recuperaron el entorno completo de Colab ni sus trazas intermedias; la primera divergencia histórica sigue abierta. La nueva ejecución Nested LOPO completó las 27 configuraciones y 675 ajustes candidatos; sus resultados se publicaron con el entorno fijado. [Diagnóstico y comparaciones](../evidencias/pi14_cierre/CP09/LEEME.md)
- **Pruebas negativas.** CP02, CP03, CP04, CP11 y CP12 se comprobaron en Streamlit. CP12 usó una copia aislada alterada. [Capturas y resultados](../evidencias/pi14_revision/C/LEEME.md)
- **CP10 — NO EJECUTADO.** El piloto con participantes quedó fuera del alcance final. No se recogieron datos empíricos de satisfacción, facilidad de uso, errores de interacción ni tiempo humano de QA. Las pruebas funcionales y los tiempos de procesamiento caracterizan el prototipo y el equipo de prueba. LOC aproxima el esfuerzo bajo un presupuesto fijo y no permite estimar minutos de revisión ahorrados.
- **Auditoría de criterios.** Los indicadores históricos de cobertura y protocolo se distinguen de umbrales de calidad. F1, AUC-ROC y Average Precision se reportan como descriptivos por proyecto y en macro. Cualquier criterio de calidad nuevo y la reformulación de OE2 requieren aprobación previa. [Tabla y criterios](../evidencias/pi14_revision/D/criterios_y_metricas.md)
- **Escalabilidad.** El lector admite 20 000 filas y 10 MiB. JM1 aportó una medición con 13 204 módulos. El ensayo nuevo midió 30 corridas secuenciales con 20 000 módulos sintéticos que repiten 18 perfiles con identificadores únicos (2,12 MiB). El flujo de lectura y validación, inferencia comparativa, calibración, rankings y serialización CSV obtuvo **p95 67,837039 s** y **mediana 64,824879 s** en Windows 10, Python 3.13, Ryzen 5 3600, 12 procesadores lógicos y unos 16 GiB de RAM. El total excluye arranque, espera del servidor, persistencia, inferencia adicional del ranking operativo, transferencia y renderizado. Parte de las corridas coincidió con diagnóstico local. El plan no fija una meta de tiempo para ese volumen. [Mediciones crudas, estadísticas y entorno](../evidencias/pi14_cierre/escalabilidad/LEEME.md)
- **Extracción.** Lizard 1.25.0 se ejecutó sobre dos funciones C y produjo NLOC, complejidad ciclomática y tokens. La equivalencia con las 21 entradas del modelo está pendiente. La demostración es independiente de Streamlit. [Mapeo y reproducción](../evidencias/pi14_cierre/metricas/LEEME.md)
- **OE4.** La comparación exploratoria frente a ManualUp y el análisis de cohortes tienen un alcance distinto de la validación del prototipo. [Alcance experimental](../evidencias/pi14_revision/E/escalabilidad_y_OE4.md) · [Matriz final](../evidencias/pi14_cierre/INFORME.md)

## 6. Reejecución completa OE3 de PI15

La búsqueda Nested LOPO completa de PI15 utiliza 27 candidatos por búsqueda, cinco proyectos externos, selección por algoritmo dentro de las fuentes, semilla 42 y dependencias fijadas. Para OE3 se recomienda usar los resultados nuevos por proyecto y sus promedios macro, conservando las tablas históricas de las secciones anteriores como antecedente. La nueva selección cambia el orden de F1 macro a XGBoost, SVM y Random Forest. El rendimiento de la receta fija E6 y la comparación exploratoria con ManualUp conservan sus protocolos. [Resultados y comparación histórica](../evidencias/pi15/oe3/RESULTADOS_OE3.md) · [Protocolo y entorno](../evidencias/pi15/oe3/LEEME.md).

La ejecución completa permite regenerar OE3 en el entorno fijado. La reproducción exacta del entorno original de Colab continúa sin acreditarse y una sola nueva corrida completa no demuestra repetibilidad íntegra de la búsqueda. [Diagnóstico previo por etapas](../evidencias/pi14_cierre/CP09/LEEME.md).
