# PDS-QA — Predicción de defectos de software para aseguramiento de calidad

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-cc233b) ![Estado](https://img.shields.io/badge/Estado-Prototipo_PI8-informational)

Prototipo web de tesis (T2, UNMSM). Permite que un analista SQA cargue un **CSV con 21 métricas estáticas compatibles con NASA/PROMISE**, obtenga una **clasificación binaria de propensión a defectos**, consulte un **ranking**, exporte el CSV y revise la **trazabilidad SQLite**.

**No inspecciona código fuente, repositorios Git ni archivos Java.** No localiza ni confirma defectos; solo estima propensión a partir de métricas históricas.

## Inicio rápido

Recomendado: Python **3.12**. Conserva las versiones exactas de scikit-learn e imbalanced-learn usadas para generar el `.joblib`.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Abre la dirección local que indique Streamlit, normalmente `http://localhost:8501`.

> **Compatibilidad del modelo:** `scikit-learn==1.6.1` y `imbalanced-learn==0.14.2` son obligatorias. El modelo fue entrenado con esas versiones en Colab v11. Una versión distinta puede provocar fallos de deserialización o resultados incorrectos. Este prototipo comprueba versiones antes de cargar el artefacto.

## Demostración de PI8

1. **Inicio:** confirma `SVM · E7_SMOTE_RF`, descarga la plantilla.
2. **Carga:** selecciona `data/sample/ejemplo_carga.csv` (18 registros ilustrativos) y pulsa **Validar archivo**.
3. **Validación:** observa las 21 columnas, SHA-256 y vista previa; pulsa **Ejecutar predicción y guardar evidencia**.
4. **Resultados:** observa clases 0/1, `score_riesgo` y `prioridad`; descarga el ranking CSV.
5. **Historial:** consulta el registro, SHA-256, fecha UTC y predicciones guardadas en SQLite.
6. **Ayuda:** verifica alcances y límites de interpretación.

Las filas del ejemplo se usan exclusivamente para probar el flujo funcional y **no** sirven para medir precisión del modelo.

## Modelo y datos

- **Algoritmo del pipeline:** SVM; balanceo **SMOTE** durante entrenamiento; selección de características mediante **Random Forest**.
- **Entrenamiento histórico:** CM1, JM1, KC1, KC2 y PC1; evaluación con validación anidada dejando un proyecto fuera (CPDP).
- **Criterio de selección:** promedio no ponderado del F1 de la clase defectuosa entre los proyectos, con desempate por Average Precision y AUC-ROC.
- **F1 de selección reportado:** `0.39725`; **no** equivale a la exactitud esperada para cualquier nuevo proyecto ni es una prueba independiente del `.joblib` entrenado con los cinco proyectos.
- **Evaluación QA:** en los resultados externos la priorización por ML **no superó sistemáticamente** la selección por líneas de código.
- **Auditoría:** la verificación humana de origen, etiquetas y alias de métricas figura **pendiente** (`documentally_verified: false`).

**`score_riesgo`:** margen de decisión SVM *sin calibrar*; puede ser negativo o positivo, no está entre 0 y 1 ni significa «porcentaje de probabilidad de defecto». El ranking ordena de mayor a menor margen.

Solo usar métricas con **definiciones, granularidad y unidades compatibles**. Una nueva app o lenguaje de programación puede producir métricas con una distribución diferente; no se garantiza desempeño universal. Las columnas opcionales `defects` / `problems`, si existen, se ignoran para predecir.

### Estructura del repositorio

```text
PDS_QA_Streamlit/
├── app.py                         # M01/UI01–UI06: interfaz Streamlit
├── src/pds/
│   ├── service.py                 # M02: orquestación
│   ├── validation.py              # M03: lectura y validación de 21 métricas
│   ├── model.py                   # M05: carga y verificación del pipeline
│   ├── prediction.py              # M04/M06/M07: inferencia, ranking, exportación
│   └── persistence.py             # M08: trazabilidad SQLite
├── artifacts/models/
│   ├── modelo_predictivo_pds.joblib
│   ├── metadatos_modelo.json
│   └── integridad_modelo.json
├── data/sample/                   # Plantilla y CSV ilustrativo
├── docs/                          # DDL, trazabilidad y criterios metodológicos
├── research/                      # Código y síntesis reproducible del Colab v11
├── tests/                         # Pruebas unitarias y de integración
├── requirements.txt
└── .github/workflows/tests.yml
```

## Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Incluye pruebas de validación de CSV, normalización, rechazo de entradas incompatibles, inferencia con *pipeline simulado*, ranking, exportación y persistencia SQLite, así como una prueba de integración con el modelo real cuando las dependencias sean compatibles.

## Trazabilidad y privacidad

SQLite registra por ejecución: identificador UUID, fecha UTC, nombre del CSV, SHA-256 del contenido, SHA-256 del artefacto, algoritmo, escenario, cantidad de registros, predicciones y ranking. No guarda el CSV íntegro ni las 21 características. **Sí conserva `id_modulo`: evita utilizar datos sensibles como identificadores.** La base de datos local queda fuera de Git por `.gitignore`.

La huella SHA-256 sirve para comprobar integridad de archivos, **no garantiza la procedencia** del modelo. El `.joblib` procede del experimento científico de entrenamiento CPDP; **nunca aceptes modelos `.joblib` cargados por usuarios o fuentes no confiables**, porque deserializarlos puede ejecutar código.

## Ejecución y despliegue

Para la demostración académica se recomienda ejecutar la aplicación localmente (`streamlit run app.py`). Si se despliega en Streamlit Community Cloud, debe considerarse que la base SQLite de la instancia puede reiniciarse tras inactividad y no debe presentarse como almacenamiento persistente de producción.

## Referencias de la investigación

El documento [`docs/METODOLOGIA_Y_LIMITES.md`](docs/METODOLOGIA_Y_LIMITES.md) describe DSR, CRISP-DM, CPDP y los resultados que sí pueden defenderse. Los datos originales no se versionan aquí; ver la fuente y las huellas en `research/fuentes_y_hashes.csv`.

**Licencias y autoría:** no se ha incorporado una licencia de código abierto por defecto. La titular del proyecto debe decidir las condiciones de reutilización antes de publicarlo; un repositorio visible públicamente no concede por sí mismo permisos generales de uso. Los derechos y condiciones de los materiales originales, datasets y dependencias deben respetarse por separado.
