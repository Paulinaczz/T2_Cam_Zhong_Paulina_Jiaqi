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

### A. Selección de la receta ganadora (`E6_ADASYN_MI`)
- **Pipeline seleccionado:** Clasificador Support Vector Machine (`SVM`) con sobremuestreo adaptativo `ADASYN` y selección de características por Información Mutua (`SelectKBest` con `mutual_info_classif`).
- **Criterio de selección:** Promedio no ponderado del F1 de la clase defectuosa entre proyectos.
- **Comparación directa E6 frente a E7:**
  - **`E6_ADASYN_MI`:** Macro F1 promedio = **0,4191** (AP: 0,3604; AUC: 0,7269; Recall: 0,6046).
  - **`E7_SMOTE_RF`:** Macro F1 promedio = **0,4146** (AP: 0,3628; AUC: 0,7260; Recall: 0,5508).
- **Prueba estadística pareada (Wilcoxon signed-rank):**
  - Estadístico \(W = 4,0\), \(p\)-valor bilateral exacto = **0,4375**.
  - **Interpretación:** No se detectó una diferencia estadísticamente significativa entre ambas recetas. Con una muestra de solo 5 proyectos, **la ausencia de significancia estadística no demuestra equivalencia**, reflejando que la ventaja observada es estrecha y dependiente del conjunto de datos.

### B. Desempeño en validación externa anidada
- En la evaluación anidada externa (*outer loop*), SVM superó a los algoritmos competidores en F1 y Recall:
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
  - **Suite Pytest:** 14 pruebas unitarias e integración aprobadas al 100 %.
- **Rendimiento (CP06 — 30 repeticiones por lote):**
  - **Lote `ejemplo_18` (18 módulos):** Tiempo de inferencia $p_{95} = \mathbf{0,0767\text{ s}}$, cumpliendo con holgura la meta exigida de $p_{95} \le 5\text{ s}$.
  - **Lote `JM1_completo` (13 204 módulos):** Tiempo de inferencia $p_{95} \approx \mathbf{50,50\text{ s}}$ (media 48,89 s; validación 0,47 s), reportado con fines descriptivos de escalabilidad.

---

## 5. Estado de Observaciones y Casos Pendientes

Para mantener el rigor académico y no declarar aprobaciones prematuras:

1. **CP09 (Sensibilidad y repetibilidad):** Permanece como pendiente formal hasta consolidar un protocolo de repetición con número suficiente de semillas e iteraciones independientes.
2. **CP10 (Aceptación y usabilidad con usuarios):** Permanece pendiente de ejecución real mediante la aplicación del instrumento validado I-05 a evaluadores y analistas de QA; no se simulan participantes ni respuestas ficticias.
3. **Capturas de rechazo de interfaz:** Las evidencias visuales cubren el flujo positivo (EVV01–EVV11). Los mensajes específicos de error para CP02, CP03 y CP11 en el navegador no disponen de captura fotográfica en esta entrega, quedando respaldados por los reportes de backend.
4. **Observaciones del asesor:** Permanecen en revisión continua hasta contar con el dictamen y aprobación formal correspondiente.
