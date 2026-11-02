# Evidencia experimental del estudio CPDP (PDS-QA)

Este directorio contiene los artefactos reproducibles del experimento científico de predicción de defectos de software entre proyectos (Cross-Project Defect Prediction - CPDP) bajo el marco DSR / CRISP-DM.

## Contenido del directorio

- `Entrenamiento_Prediccion_Defectos.ipynb`: **Cuaderno Jupyter principal** con la ejecución interactiva completa, visualizaciones, validación anidada, contraste estadístico pareado y análisis de esfuerzo.
- `entrenamiento_defectos.py`: Script modular de reentrenamiento y validación de pipelines CPDP.
  > **Nota sobre el ranking híbrido:** El script `entrenamiento_defectos.py` ejecuta el pipeline central de búsqueda y selección de modelos; **el cuaderno `Entrenamiento_Prediccion_Defectos.ipynb` es la fuente completa del experimento adicional de ranking híbrido** (sección de ranking consciente del esfuerzo de QA y combinación lineal de rangos con LOC).
- `NOTAS_METODOLOGICAS.json`: Pautas de interpretación metodológica y límites de validez de las métricas.
- `candidatos_y_hashes.csv`: Huellas SHA-256 de los modelos candidatos E6 y E7.
- `auditoria/`:
  - `resumen_cohortes.json`: Auditoría de deduplicación global previa a las particiones (17 442 filas originales -> 11 690 instancias únicas).
  - `dedup_principal_por_proyecto.csv`: Distribución de filas y prevalencia deduplicada por proyecto (CM1, JM1, KC1, KC2, PC1).
  - `dedup_sensibilidad_por_proyecto.csv`: Análisis de sensibilidad excluyendo grupos con etiquetas contradictorias.
  - `grupos_etiquetas_contradictorias.csv`: Registro de las 121 tuplas con igual vector de 21 métricas pero etiquetas dispares.
  - `impacto_conflictos_por_proyecto.csv`: Cuantificación de filas en conflicto por proyecto.
  - `solapamiento_original.csv`, `solapamiento_deduplicado.csv`: Verificación de solapamiento entre proyectos.
- `experimentos/`:
  - `comparacion_configuraciones/`:
    - `deduplicado/E6_vs_E7_por_proyecto.csv`: Rendimiento detallado por proyecto de SVM en E6_ADASYN_MI vs E7_SMOTE_RF.
    - `deduplicado/prueba_pareada_deduplicado.csv`: Prueba pareada de Wilcoxon sobre los 5 proyectos (E6 F1: 0,4191 vs E7 F1: 0,4146; W = 4,0, p = 0,4375).
    - Sensibilidad en cohortes `sin_deduplicar` y `sin_grupos_conflictivos`.
  - `validacion_anidada/`:
    - `comparacion_algoritmos_outer.csv`: Evaluación externa Nested Leave-One-Project-Out comparando SVM, Random Forest y XGBoost.
    - `resumen_algoritmos_externos.csv`: Resumen macro outer (SVM F1: 0,4122; XGBoost F1: 0,3983; RF F1: 0,3606).
    - `resumen_final.json`: Metadatos de la selección global (E6_ADASYN_MI ganador).
  - `QA_promedios_proyecto.csv`: Comparativa de reglas operativas (ML vs ManualUp vs LOC descendente vs Azar) evaluando Recall@10%, 20%, 30% de módulos y de LOC, y Popt.
  - `ranking_consciente_del_esfuerzo/`:
    - `comparacion_promedio.csv` y `resultados_por_proyecto.csv`: Evaluación del ranking híbrido combinando margen SVM y tamaño de módulo.
  - `recall_por_modulos.png` y `recall_por_LOC.png`: Curvas comparativas de priorización por esfuerzo.
