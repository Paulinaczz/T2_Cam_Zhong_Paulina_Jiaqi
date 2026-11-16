# CP09 · Diagnóstico de la diferencia histórica

## Controles verificados

| Componente | Hallazgo |
|---|---|
| Datos y preprocesamiento | Coinciden los cinco SHA-256 originales y la huella ordenada de matrices X y etiquetas por proyecto. La configuración serializada también coincide con la histórica (SHA-256 1d813bae1fa9f91a944be4e355ff6887bde6af8d09a70f9d71df6ac7ea3db51e). |
| Duplicados y conflictos | Se aplica la misma deduplicación global determinista sin consultar la etiqueta para elegir la fila. La cohorte principal tiene 11 690 filas y conserva una representante de cada grupo conflictivo. La cohorte secundaria excluye 121 grupos y queda fuera de este contraste. |
| Pliegues | Coinciden el orden de proyectos en entrenamiento externo, el número de filas y positivos de prueba y el orden de los proyectos de validación interna. Se comprobó solapamiento cero. Los tamaños externos son CM1 439, JM1 8 787, KC1 1 166, KC2 351 y PC1 947. Los pliegues internos archivados se inspeccionaron, sin reentrenarlos en esta revisión. |
| Selección e hiperparámetros | Cada checkpoint externo conserva 27 candidatos. Al aplicar el selector a los checkpoints archivados se recuperan las 15 recetas por proyecto y algoritmo y el F1 interno que registró la tabla histórica. El contraste de sintaxis Python confirma las mismas constantes, construcción de pipeline, métricas y funciones de selección entre el script, el notebook del repositorio y el notebook original disponible. |
| Semillas | 42 para deduplicación, el estimador de MI, el RF selector, SMOTE/ADASYN y el estimador final. Los pliegues por proyecto son deterministas, sin partición aleatoria. Los generadores de ranking aleatorio y bootstrap pertenecen al análisis de esfuerzo. La serie con semilla 43 cambia el entrenamiento, con deduplicación y pliegues fijos. |
| Entorno | El original se ejecutó en Colab. Su salida registra scikit-learn 1.6.1, imbalanced-learn 0.14.2, XGBoost 3.4.1 y pandas 2.2.3. Los tres primeros coinciden con los locales. El ensayo local usa Windows, Python 3.13.0, pandas 2.3.3, NumPy 2.5.5, SciPy 1.18.1 y un hilo. El registro histórico consultado no fija la versión exacta de Python, NumPy, SciPy, bibliotecas numéricas nativas ni su configuración de hilos. |
| Diferencia de procedimiento | El Colab original ejecutó la selección Nested LOPO completa y reportó 76,6 min para esa celda. La revisión reentrenó las recetas archivadas, conservando los mismos proyectos, orden y código de preparación, ajuste y evaluación externos. La omisión de la búsqueda interna limita el alcance de CP09. Las recetas y parámetros externos recuperados coinciden. |

Recetas nominales comprobadas: imputación por mediana, escalado estándar, selector de passthrough, MI con k=10 o RF selector de 100 árboles con umbral mediana, luego passthrough, SMOTE o ADASYN con tres vecinos. Estimadores: SVM RBF C=1 y gamma scale, RF de 200 árboles y profundidad 12, XGBoost de 160 estimadores, profundidad 3, tasa 0,1 y árbol hist. El detalle permanece en la implementación versionada.

## Experimentos de aislamiento

Se repitieron tres recetas de Random Forest (dos discordantes, CM1 y PC1, y una concordante, JM1). Se cambió un factor por vez:

- **pandas 2.2.3.** Las nueve métricas de las tres recetas coincidieron exactamente con la base local. El cambio aislado no explica la discrepancia.
- **Backend alternativo de distancias de scikit-learn.** Deshabilitar la reducción Cython de distancias mantuvo CM1 y JM1 e hizo variar PC1. En PC1 el F1 pasó de 0,334975 a 0,311558, frente a 0,291457 histórico. La perturbación demuestra sensibilidad numérica de esa receta, pero no reproduce el histórico ni identifica su backend efectivo.

[Control y resultados base](diagnostico/base/control.json) · [Métricas base](diagnostico/base/metricas.csv) · [pandas histórico](diagnostico/pandas223/metricas.csv) · [Backend alternativo](diagnostico/distancias_alternativas/metricas.csv) · [Lanzador de diagnóstico](diagnostico_cp09.py)

## Dictamen

**CP09 parcial.** Se comprobó repetibilidad local con semilla y entorno fijos. La causa histórica exacta continúa abierta. Datos, recetas y código externo nominal coinciden; el cambio aislado de pandas no reprodujo la diferencia. La sensibilidad del backend demuestra una vía plausible de variación, sin atribuirla a Colab. Para cerrar la atribución se necesita recuperar o volver a ejecutar el entorno histórico con versiones nativas y de Python detalladas y comparar salidas intermedias por etapa (matriz escalada, columnas seleccionadas, resultados del balanceo y predicciones), antes de repetir la búsqueda de 27 configuraciones. Se preservaron ambas series.
