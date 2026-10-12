# Matriz técnica de trazabilidad PI8

| Requisito (PI5) | Módulo de PI6 | Implementación | Evidencia verificable |
|---|---|---|---|
| RF01 Carga CSV | M01/M02 | `app.py` UI02, `service.prepare_csv()` | CSV de prueba / test de lector |
| RF02 Validación | M03 | `validation.validate_input()` | Mensajes de faltantes, duplicados y tipos |
| RF03 Preprocesamiento | M04 | `modelo_general_cpdp.joblib` con imputer/scaler/selector | Pasos `named_steps`, test integración |
| RF04 Inferencia | M05/M06 | `model.load_model()`, `prediction.predict()` | Resultado reproducible, no se reentrena |
| RF05 Clasificación | M06 | `clase_predicha` 0/1 | Tabla UI04 y exportación |
| RF06 Score | M06 | `score_riesgo=decision_function` | `tipo_score=margen_svm_no_calibrado` |
| RF07 Priorizar | M07 | Orden estable descendente `score_riesgo` | Columna `prioridad` |
| RF08 Exportar | M07 | `csv_results`, `st.download_button` | CSV resultante |
| Trazabilidad | M08 | `persistence`, `schema.sql` | UI05, SQLite y test de registro |

**Secuencia correcta:** cargar y verificar pipeline → leer CSV → validar → ejecutar transformaciones *dentro del pipeline ya cargado* → predecir → ordenar → registrar → exportar.

No se implementa extracción de métricas desde el código fuente ni API REST. Persistencia local de prototipo (no producción). El módulo de entrenamiento se mantiene separado dentro de `research/`.
