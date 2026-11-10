# Evaluación Experimental de Priorización por Esfuerzo (CPDP)

Este directorio contiene los scripts reproducibles y los resultados experimentales de la evaluación de priorización de inspección de código consciente del esfuerzo (*effort-aware defect prediction*) en el marco de la predicción de defectos entre proyectos (*Cross-Project Defect Prediction*, CPDP).

## 1. Contexto Metodológico y Separación de Alcance

- **Modelo operativo de despliegue:** La aplicación interactiva (Streamlit) utiliza el pipeline **E6_ADASYN_MI** (clasificador SVM con sobremuestreo ADASYN y selección de 21 métricas mediante información mutua), ordenando los módulos por el margen de decisión de la función de soporte (`decision_function`).
- **Investigación científica de esfuerzo:** Siguiendo las observaciones del asesor respecto al sesgo por tamaño de módulo (LOC), se evaluó de manera experimental e independiente una estrategia de **probabilidad calibrada por LOC** ($\widehat{P}(\text{defecto}) / \text{LOC}$), contrastándola con la heurística de referencia **ManualUp** (ordenar por LOC ascendente) y otras líneas base.
- **Sin fuga de información:** La calibración de probabilidades se ajusta exclusivamente sobre los proyectos fuente (*out-of-fold*) mediante regresión logística sigmoide (método de Platt). El proyecto destino nunca participa en el entrenamiento ni en la calibración.

## 2. Scripts Reproducibles

- `cpdp_core.py`: Definición de las 21 métricas estándar, preprocesamiento, esquemas de muestreo/selección y validación Leave-One-Project-Out (LOPO).
- `cpdp_evaluacion.py`: Auditoría de duplicados, análisis de etiquetas contradictorias y cálculo de métricas de inspección por módulos y por esfuerzo (LOC).
- `cpdp_estrategia_esfuerzo.py`: Implementación del ranking por probabilidad calibrada dividida entre LOC, cálculo de Recall@k% LOC, $P_{\text{opt}}$ e intervalos bootstrap al 95 % (1000 iteraciones).
- `plan_analisis_estrategia_esfuerzo.json`: Registro formal del plan de análisis y criterios de comparación.
- `referencia_experimental_incluida.json`: Metadatos y huellas de las selecciones experimentales previas.

## 3. Resultados en la Cohorte Principal (`principal_deduplicada/`)

En la cohorte principal (donde se conserva un único registro por vector de métricas idéntico sin consultar la etiqueta):

| Métrica / Parámetro | E6 Calibrado / LOC | Heurística ManualUp | Diferencia ($\Delta$) | Interpretación |
| :--- | :--- | :--- | :--- | :--- |
| **Recall@20 % LOC (Promedio macro)** | **29,09 %** | **28,74 %** | **+0,36 p.p.** | Diferencia marginal (+0,00356) |
| **Recall@10 % LOC (Promedio macro)** | 15,39 % | 15,25 % | +0,15 p.p. | Comportamiento similar |
| **$P_{\text{opt}}$ normalizado (0–20 % LOC)** | 25,50 % | 25,71 % | -0,21 p.p. | ManualUp ligeramente superior |
| **$P_{\text{opt}}$ normalizado (0–100 % LOC)** | 62,39 % | 62,27 % | +0,12 p.p. | Empate práctico |
| **Proyectos con $\Delta > 0$ a favor de ML** | 2 de 5 (CM1: +4,35 p.p., JM1: +0,85 p.p.) | — | — | CM1 y JM1 muestran leve ventaja |
| **Proyectos con $\Delta < 0$ a favor de ManualUp** | — | 3 de 5 (KC1: -0,97 p.p., KC2: -1,02 p.p., PC1: -1,43 p.p.) | — | ManualUp supera en 3 proyectos |

### Análisis Estadístico de Intervalos Bootstrap (IC 95 %)

Para cada proyecto, se estimó la diferencia mediante remuestreo bootstrap con 1000 repeticiones:
- **CM1:** $\Delta = +4,35\text{ p.p.}$, IC 95 %: $[-5,56\text{ p.p.},\; +11,63\text{ p.p.}]$ (incluye el 0)
- **JM1:** $\Delta = +0,85\text{ p.p.}$, IC 95 %: $[-0,83\text{ p.p.},\; +2,30\text{ p.p.}]$ (incluye el 0)
- **KC1:** $\Delta = -0,97\text{ p.p.}$, IC 95 %: $[-3,04\text{ p.p.},\; +1,06\text{ p.p.}]$ (incluye el 0)
- **KC2:** $\Delta = -1,02\text{ p.p.}$, IC 95 %: $[-7,22\text{ p.p.},\; +1,92\text{ p.p.}]$ (incluye el 0)
- **PC1:** $\Delta = -1,43\text{ p.p.}$, IC 95 %: $[-4,29\text{ p.p.},\; +3,80\text{ p.p.}]$ (incluye el 0)

## 4. Conclusiones Científicas

1. **Ausencia de superioridad consistente:** Dado que los intervalos bootstrap de confianza al 95 % de las diferencias incluyen el cero en la totalidad de los proyectos evaluados, y que el clasificador supera a ManualUp en solo 2 de los 5 casos, **no existe evidencia estadística suficiente para sostener que la estrategia de aprendizaje automático sea consistentemente superior a la heurística de inspeccionar módulos pequeños (ManualUp)** bajo un presupuesto de inspección del 20 % de LOC.
2. **$P_{\text{opt}}$:** En el rango de inspección operativa (0–20 % del esfuerzo), la métrica $P_{\text{opt}}$ no favorece al modelo predictivo frente a la regla ManualUp.
3. **Implicancia para el artefacto:** Estos hallazgos validan la pertinencia de mantener el modelo serializado en su forma actual para priorización operativa por margen, reportando con total transparencia los límites del modelado predictivo frente a reglas deterministas de tamaño de código.
