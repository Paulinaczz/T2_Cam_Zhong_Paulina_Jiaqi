# Criterios OE1–OE3 y resultados descriptivos históricos

Fuentes documentales: plan PI11–PI12 §1.2 y §2.3, revisión del profesor O4–O5. Fuente de métricas: [comparación externa guardada](../../../research/experimentos/validacion_anidada/comparacion_algoritmos_outer.csv). La receta se seleccionó por algoritmo dentro de cada pliegue externo usando los proyectos fuente. Las cifras se refieren a ese procedimiento Nested LOPO deduplicado; el macro asigna peso igual a cada uno de los cinco proyectos. No corresponde al artefacto global E6 calibrado ni a un nuevo entrenamiento de este bloque.

| OE | Criterio previo del plan | Acción pendiente de aprobación |
|---|---|---|
| OE1 | 3 de 3 familias con ficha y fuentes trazables | Evaluar la calidad de referencias y coherencia del protocolo; el conteo por sí solo acredita cobertura |
| OE2 | Cinco proyectos reservados externamente y cero vectores X compartidos entre entrenamiento y prueba | Actualizar formalmente la formulación de 80/20 a Nested LOPO, justificando la generalización entre proyectos |
| OE3 | 27 configuraciones verificables, 21 métricas y esquema completo | Evaluar calidad frente a SVM base en los mismos folds con diferencias F1/AP e intervalos, como propone O5 |

El plan y la revisión consultados no fijan cortes cuantitativos previos de F1, AUC o AP. Se reportan como descriptivos. Cualquier referencia cuantitativa futura requiere justificación externa y aprobación antes de una evaluación nueva. El criterio ΔRecall@20%LOC del plan pertenece a OE4.

## Tabla externa por proyecto y promedio macro

| Proyecto | Algoritmo | Escenario | F1 | AUC-ROC | AP |
|---|---|---|---:|---:|---:|
| CM1 | Random Forest | E6_ADASYN_MI | 0.153846 | 0.639119 | 0.195024 |
| CM1 | SVM | E7_SMOTE_RF | 0.333333 | 0.766567 | 0.258502 |
| CM1 | XGBoost | E5_SMOTE_MI | 0.348485 | 0.750940 | 0.258292 |
| JM1 | Random Forest | E5_SMOTE_MI | 0.365784 | 0.614486 | 0.334954 |
| JM1 | SVM | E5_SMOTE_MI | 0.423562 | 0.658295 | 0.357689 |
| JM1 | XGBoost | E5_SMOTE_MI | 0.383292 | 0.638178 | 0.363189 |
| KC1 | Random Forest | E7_SMOTE_RF | 0.358730 | 0.594166 | 0.356290 |
| KC1 | SVM | E6_ADASYN_MI | 0.422018 | 0.642151 | 0.385212 |
| KC1 | XGBoost | E6_ADASYN_MI | 0.405229 | 0.617052 | 0.368892 |
| KC2 | Random Forest | E6_ADASYN_MI | 0.633333 | 0.819916 | 0.673860 |
| KC2 | SVM | E8_ADASYN_RF | 0.628352 | 0.802896 | 0.550351 |
| KC2 | XGBoost | E6_ADASYN_MI | 0.596330 | 0.803864 | 0.652409 |
| PC1 | Random Forest | E2_ADASYN | 0.291457 | 0.781683 | 0.263334 |
| PC1 | SVM | E8_ADASYN_RF | 0.253846 | 0.768456 | 0.193456 |
| PC1 | XGBoost | E8_ADASYN_RF | 0.258065 | 0.751385 | 0.221978 |
| MACRO | Random Forest | — | 0.360630 | 0.689874 | 0.364693 |
| MACRO | SVM | — | 0.412223 | 0.727673 | 0.349042 |
| MACRO | XGBoost | — | 0.398280 | 0.712284 | 0.372952 |

[CSV](metricas_nested_lopo.csv).
