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

## 3. Evaluación de priorización y esfuerzo de QA

Se evaluó la eficacia de priorización bajo dos métricas de presupuesto: porcentaje de módulos inspeccionados y porcentaje de líneas de código (LOC).

| Estrategia de priorización | Recall@20% Módulos | Recall@20% LOC (módulos completos) | Popt (0–20%) |
| :--- | :---: | :---: | :---: |
| **ManualUp (ordenar por LOC ascendente)** | 6,24 % | **28,74 %** | **0,2571** |
| **Ranking Híbrido (ML + LOC)** | 6,47 % | 25,13 % | 0,2186 |
| **ML puro (Margen SVM)** | **42,39 %** | 18,02 % | 0,1519 |
| **LOC descendente (inspeccionar más grandes)** | 44,20 % | 9,40 % | 0,0607 |
| **Referencia aleatoria** | 20,12 % | 19,87 % | 0,1698 |

### Conclusiones clave sobre el esfuerzo:
1. **ManualUp superó a ML cuando el costo se mide en LOC:** Inspeccionar módulos pequeños primero (`ManualUp`) capturó el 28,74 % de defectos al 20 % de LOC acumuladas, superando tanto al modelo ML (18,02 %) como al ranking híbrido (25,13 %).
2. **ML es superior cuando el presupuesto se fija en cantidad de módulos:** Al revisar el 20 % de los módulos de un proyecto, ML detectó el 42,39 % de los defectos frente al 6,24 % de ManualUp.
3. **Ausencia de garantía de ahorro universal:** El modelo predictivo **no garantiza un ahorro sistemático de tiempo ni una mejora universal frente a ManualUp** en contextos donde el esfuerzo de revisión está estrictamente ligado al tamaño del código.

---

## 4. Limitaciones y alcances operativos

1. **Dependencia de métricas calculadas previamente:** El software no inspecciona código fuente ni repositorios Git; requiere que las **21 métricas estáticas compatibles** se hayan calculado y tabulado previamente con definiciones homogéneas.
2. **Procedencia documental de los datos:** Los datasets provienen del repositorio público NASA/PROMISE sin auditoría documental primaria del creador original (`documentally_verified: false`). Existen alias (p. ej. `locCodeAndComment`) y 121 tuplas con métricas idénticas y etiquetas dispares que fueron identificadas durante la auditoría.
3. **Naturaleza del score:** El valor `score_riesgo` es el margen funcional de decisión SVM sin calibrar; **no representa una probabilidad porcentual de defecto**. Se emplea estrictamente como criterio de ordenación relativa.
4. **Juicio profesional de SQA:** La clasificación como «potencialmente defectuoso» es una estimación estadística y nunca sustituye las pruebas funcionales, la inspección humana ni el juicio de los analistas de calidad de software.
