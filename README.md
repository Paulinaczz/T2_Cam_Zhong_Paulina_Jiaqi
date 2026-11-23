# PDS-QA — Predicción de Defectos de Software para Aseguramiento de Calidad

![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue) ![Streamlit](https://img.shields.io/badge/UI-Streamlit-cc233b) ![Integridad](https://img.shields.io/badge/Modelo-SHA256%20Verificado-success) ![Validación](https://img.shields.io/badge/Validación-PI13%20%7C%20PI14-informational)

Prototipo software desarrollado en el marco de la tesis de licenciatura en Ingeniería de Software (UNMSM). Su propósito es apoyar los procesos de aseguramiento de calidad de software (SQA) mediante la **clasificación y ordenación relativa de módulos de software propensos a defectos**, a partir de **21 métricas estáticas compatibles con el estándar NASA/PROMISE**.

> **Alcance operativo y delimitación técnica:** El sistema **no inspecciona código fuente ni analiza repositorios Git directamente**. Requiere como entrada un archivo CSV estructurado con las 21 métricas estáticas ya calculadas. No confirma ni localiza fallos específicos en el código; estima la propensión al riesgo con fines de optimización de esfuerzos de inspección humana.

---

## 1. Inicio Rápido y Ejecución Local

### Requisitos del Sistema
- Python **3.12** o **3.13**.
- Bibliotecas obligatorias con versiones exactas: `scikit-learn==1.6.1` e `imbalanced-learn==0.14.2`. El artefacto Joblib verifica estrictamente estas dependencias y su firma SHA-256 antes de permitir la inferencia.

### Instalación y Puesta en Marcha

```powershell
# 1. Clonar el repositorio y acceder a la raíz
cd T2_Cam_Zhong_Paulina_Jiaqi

# 2. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # En Linux/macOS: source .venv/bin/activate

# 3. Instalar dependencias operativas y de desarrollo
python -m pip install -r requirements-dev.txt

# 4. Iniciar la aplicación interactiva Streamlit
streamlit run app.py
```

La interfaz web se iniciará automáticamente en `http://localhost:8501`.

---

## 2. Flujo Operativo en la Interfaz (Streamlit)

1. **UI01 (Inicio y Verificación):** Muestra los metadatos del pipeline activo (`SVM · E6_ADASYN_MI`), su hash criptográfico SHA-256 y permite descargar la plantilla CSV oficial.
2. **UI02 (Carga de Datos):** Permite subir archivos CSV con métricas de software (p. ej., `data/sample/ejemplo_carga.csv`).
3. **UI03 (Validación de Esquema):** Valida las 21 columnas requeridas, tipo de datos numéricos y ausencia de duplicados, mostrando el hash SHA-256 del archivo cargado.
4. **UI04 (Inferencia, Priorización y Comparativa):** Ejecuta la predicción mediante el clasificador SVM. Ofrece dos pestañas: **Ranking Operativo** (orden decreciente por margen SVM) y **Comparación de Estrategias** (en atención a la **Observación O1**, contrasta el margen SVM, la densidad experimental de probabilidad calibrada por LOC y la heurística ManualUp). Permite exportar ambos rankings en CSV sanitizado.
5. **UI05 (Historial y Trazabilidad):** Consulta el registro auditable persistido en base de datos SQLite aislada (identificador UUID, marcas de tiempo UTC, hashes y estado de ejecución).
6. **UI06 (Guía y Limitaciones):** Explica el significado del margen de soporte, la calibración Platt y advierte sobre los límites empíricos del modelo frente a ManualUp.

---

## 3. Modelo Predictivo y Hallazgos Científicos

### A. Pipeline Desplegado (`E6_ADASYN_MI`)
- **Algoritmo:** Support Vector Machine (`SVM`) con kernel RBF.
- **Técnica de balanceo:** Sobremuestreo adaptativo `ADASYN` aplicado durante el entrenamiento.
- **Selección de características:** `SelectKBest` fundamentado en Información Mutua (`mutual_info_classif`).
- **Hash de integridad SHA-256:** `5a420bc52058979620cd2b86cbca01536e17be931056327ed715256719c8023f`.
- **Score operativo:** Margen funcional de la función de decisión (`decision_function`). El ranking operativo ordena los módulos de mayor a menor margen.

### B. Evaluación Experimental y Comparación con la Heurística ManualUp
En el marco de la investigación en Google Colab sobre predicción entre proyectos (CPDP con CM1, JM1, KC1, KC2 y PC1 deduplicados), se evaluó una estrategia de **probabilidad calibrada por líneas de código ($\widehat{P} / \text{LOC}$)**:

| Métrica / Estrategia | E6 Calibrado / LOC | ManualUp (LOC asc.) | Diferencia ($\Delta$) | Intervalo Bootstrap (IC 95 %) |
| :--- | :--- | :--- | :--- | :--- |
| **Recall@20 % LOC (Promedio)** | **29,09 %** | **28,74 %** | **+0,36 p.p.** | CM1: [-5,56, +11,63] p.p. |
| **Recall@10 % LOC (Promedio)** | 15,39 % | 15,25 % | +0,15 p.p. | JM1: [-0,83, +2,30] p.p. |
| **$P_{\text{opt}}$ normalizado (0–20 %)** | 25,50 % | **25,71 %** | -0,21 p.p. | KC1: [-3,04, +1,06] p.p. |
| **Proyectos ganados** | 2 de 5 (CM1, JM1) | **3 de 5** (KC1, KC2, PC1) | — | Todos incluyen el 0 |

> **Conclusión metodológica:** La diferencia media en Recall@20 % LOC es de +0,36 puntos porcentuales y los intervalos bootstrap al 95 % de las diferencias incluyen el cero en la totalidad de los proyectos. Por lo tanto, **no existe evidencia estadística suficiente para sostener una superioridad consistente del aprendizaje automático frente a la regla determinista de priorizar módulos pequeños (ManualUp)**. Estos resultados forman parte del análisis experimental de investigación y se documentan con rigurosidad académica en [docs/METODOLOGIA_Y_LIMITES.md](docs/METODOLOGIA_Y_LIMITES.md).

### C. Artefacto Calibrador para Inferencia (Observación O1)
- **Calibrador serializado:** `artifacts/models/calibrador_probabilidad_e6.joblib` (SHA-256: `a15aab94b20b2826f0ffd07e13a23bd36600743d26ec8657196b3f16f6884d19`).
- **Función de calibración:** Sigmoide de Platt ajustada sobre los 11 690 márgenes *out-of-fold* del conjunto histórico ($\beta_1 = 0,7743$, $\beta_0 = -1,2852$). Mapea el margen SVM continuo a una probabilidad en $[0, 1]$.
- **Integridad del pipeline base:** El modelo predictivo principal `modelo_predictivo_pds.joblib` (SHA-256: `5a420bc5...`) permanece 100 % intacto e inalterado.

---

## 4. Evidencias de Validación Técnica y Operativa (PI13–PI14)

Los informes formales se encuentran disponibles en:
- [T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf](docs/avances/T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf) / [.docx](docs/avances/T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.docx)
- [T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf](docs/avances/T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf) / [.docx](docs/avances/T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.docx)
- [T2_ADENDA_CAPTURAS_RESUMEN_10NOV2026.md](docs/avances/T2_ADENDA_CAPTURAS_RESUMEN_10NOV2026.md)

### Resumen de Pruebas Ejecutadas

| Caso | Tipo | Resultado Técnico Obtenido | Archivos de Respaldo |
| :--- | :--- | :--- | :--- |
| **CP01** | Funcional | 18 módulos y 21 métricas validados. Se verificaron el ranking SVM, el ranking calibrado/LOC y ManualUp. | [Matriz exportada](evidencias/pi13/o1_20261115_181721/CP01_comparacion.csv) |
| **CP02** | Seguridad | Rechazo inmediato de CSV sin columna `loc`; SQLite inalterada | `evidencias/pi13/validacion_local/casos/CP02/` |
| **CP03** | Seguridad | Rechazo controlado de valores infinitos (`inf`) y datos alfanuméricos | `evidencias/pi13/validacion_local/casos/CP03/` |
| **CP04** | Seguridad | Escapado de fórmulas CSV (`=1+2` sanitizado a `'=1+2`) | `evidencias/pi13/validacion_local/casos/CP04/` |
| **CP05** | Funcional | Ejecución COMPLETADA con UUID, hashes y 18 predicciones verificadas en SQLite. | [Comprobaciones](evidencias/pi13/o1_20261115_181721/CP01_CP05.json) |
| **CP06** | Rendimiento | 30 repeticiones independientes por lote. p95 del flujo comparativo de **0,096739 s** con 18 módulos y **47,783318 s** con JM1 completo (13 204 módulos). | [Mediciones](evidencias/pi13/o1_20261115_181721/CP06_mediciones.csv) · [Resumen](evidencias/pi13/o1_20261115_181721/CP06_resumen_segundos.csv) |
| **CP11** | Seguridad | Rechazo de extensiones incompatibles (`.xlsx`) e IDs duplicados | `evidencias/pi13/validacion_local/casos/CP11/` |
| **CP12** | Seguridad | Bloqueo estricto del pipeline ante alteración del hash SHA-256 | `evidencias/pi13/validacion_local/casos/CP12/` |
| **Pytest** | Automatizada | **15 pruebas aprobadas**, incluida la integración con E6 y las comprobaciones de calibración. | [Registro pytest](evidencias/pi13/o1_20261115_181721/suite_pytest.txt) |

El total de CP06 mide validación, inferencia comparativa, calibración, cálculo de rankings y serialización CSV. Excluye arranque, persistencia, inferencia adicional en UI04 y renderizado. La meta de 5 s corresponde al lote de 18 módulos.

La validación operativa de O1 y las [capturas reales de Streamlit](evidencias/pi13/o1_20261115_181721/capturas/) se documentan en el [índice de evidencias](evidencias/pi13/o1_20261115_181721/LEEME.md). La evaluación experimental Nested LOPO corresponde a la sección anterior. Las capturas históricas se conservan en su [índice original](evidencias/pi13/capturas/INDICE_CAPTURAS.csv).

---

## 5. Seguimiento PI13–PI14

- **UI04 — O1:** la interfaz identifica a CM1 y JM1 como los proyectos con delta positivo frente a ManualUp. Una prueba de Streamlit contrasta el texto renderizado con el CSV experimental. [Corrección y prueba](evidencias/pi14_revision/UI04/LEEME.md)
- **CP09 — parcialmente comprobado:** dos repeticiones locales con semilla 42 produjeron CSV idénticos. NumPy 2.1.3 reprodujo las tres métricas históricas de 4 de 15 recetas. Se observó sensibilidad del escalado y de ADASYN a la pila numérica. El entorno histórico de Colab sigue sin recuperarse por completo y la búsqueda Nested LOPO de 27 configuraciones está pendiente. [Diagnóstico y trazas](evidencias/pi14_cierre/CP09/LEEME.md)
- **CP10 — NO EJECUTADO:** la evaluación con participantes quedó fuera del alcance final. No hay evidencia empírica de satisfacción, facilidad de uso ni cambios en el tiempo humano de QA. [Limitaciones](docs/METODOLOGIA_Y_LIMITES.md)
- **Streamlit:** se ejecutaron CP02, CP03, CP04, CP11 y CP12 con capturas de navegador y evidencia del CSV exportado. [Registro visual](evidencias/pi14_revision/C/LEEME.md)
- **Escalabilidad:** el lector admite 20 000 filas y 10 MiB. En 30 corridas con 20 000 módulos sintéticos (2,12 MiB), el flujo comparativo obtuvo **p95 67,837039 s** y **mediana 64,824879 s** en Windows 10, Ryzen 5 3600 y unos 16 GiB de RAM. Se excluyeron arranque, espera del servidor, persistencia, inferencia adicional del ranking operativo, transferencia y renderizado. El plan no fijó una meta para ese lote. [Mediciones y entorno](evidencias/pi14_cierre/escalabilidad/LEEME.md)
- **Extracción:** Lizard 1.25.0 obtuvo NLOC, complejidad ciclomática y tokens por función en un ejemplo C. La equivalencia de las 21 métricas sigue pendiente. Streamlit sigue recibiendo métricas precalculadas. [Demostración](evidencias/pi14_cierre/metricas/LEEME.md)
- **Matriz PI13–PI14:** [comprobado, parcialmente comprobado, pendiente y no ejecutado](evidencias/pi14_cierre/INFORME.md). [Material para la tesis y la demostración](docs/cierre_tesis/INFORME_TESIS_PI13_PI14.md).

---

## 6. Estructura del Repositorio

```text
T2_Cam_Zhong_Paulina_Jiaqi/
├── app.py                                   # Aplicación interactiva Streamlit (M01/UI01–UI06)
├── src/pds/                                 # Módulos del núcleo del sistema
│   ├── errors.py                            # Excepciones tipadas de entrada y modelo
│   ├── model.py                             # Carga y verificación criptográfica del modelo E6
│   ├── persistence.py                       # Gestión de base de datos SQLite y auditoría
│   ├── prediction.py                        # Inferencia, asignación de prioridad y exportación
│   ├── service.py                           # Orquestación de servicios
│   └── validation.py                        # Validación estricta de 21 métricas y saneamiento
├── artifacts/models/                        # Artefacto serializado Joblib y metadatos oficiales
│   ├── modelo_predictivo_pds.joblib         # Pipeline E6_ADASYN_MI serializado
│   ├── metadatos_modelo.json                # Metadatos del modelo entrenado
│   └── integridad_modelo.json               # Hash SHA-256 oficial para verificación en runtime
├── data/sample/                             # Datos de muestra y plantilla
│   ├── ejemplo_carga.csv                    # CSV ilustrativo de 18 módulos
│   └── plantilla_para_streamlit.csv         # Plantilla vacía con los 21 encabezados
├── docs/                                    # Documentación técnica y avances formales
│   ├── avances/                             # Informes consolidados PI13, PI14 y adenda visual
│   ├── METODOLOGIA_Y_LIMITES.md             # Fundamentación metodológica, límites y análisis de esfuerzo
│   ├── schema.sql                           # Esquema relacional de base de datos
│   └── TRAZABILIDAD_PI8.md                  # Matriz de trazabilidad de requisitos y módulos
├── evidencias/pi13/                         # Paquete de evidencias de validación local
│   ├── capturas/                            # 11 capturas de pantalla originales e índice detallado
│   └── validacion_local/                    # Registros de ejecución, reportes CSV/JSON y suites de CP01–CP12
├── herramientas_pi13/                       # Scripts reproducibles para validación local de CP01–CP12
│   ├── ejecutar_pi13.py                     # Ejecutor automatizado de pruebas backend y rendimiento
│   └── datos/                               # Datos auxiliares (JM1 completo para CP06)
├── research/                                # Investigación experimental y cuadernos Colab
│   ├── Entrenamiento_Prediccion_Defectos.ipynb # Cuaderno oficial de entrenamiento y CPDP
│   ├── auditoria/                           # Tablas de duplicados y etiquetas contradictorias
│   └── experimentos/
│       └── estrategia_esfuerzo/             # Scripts y resultados de evaluación calibrada/LOC
├── tests/                                   # Suite de pruebas automatizadas Pytest
├── requirements.txt                         # Dependencias para despliegue en producción
├── requirements-dev.txt                     # Dependencias para desarrollo y pruebas
└── runtime.txt                              # Versión oficial de entorno Python (3.12.8)
```

---

## 7. Ejecución de Pruebas Automatizadas

```powershell
# Ejecución de la suite completa de pruebas unitarias e integración
python -m pytest -q tests

# Ejecución automatizada de validación PI13 (funcionales y seguridad)
python herramientas_pi13/ejecutar_pi13.py --repo . --modo funcionales --salida evidencias/pi13/validacion_local

# Medición de rendimiento CP06 (30 repeticiones)
python herramientas_pi13/ejecutar_pi13.py --repo . --modo rendimiento --repeticiones 30 --salida evidencias/pi13/validacion_local
```

## Versión final de tesis

La versión de referencia es [v1.0-tesis](https://github.com/Paulinaczz/T2_Cam_Zhong_Paulina_Jiaqi/releases/tag/v1.0-tesis). El entorno fijado y la búsqueda completa de 27 configuraciones Nested LOPO de PI15 están documentados en [resultados OE3](evidencias/pi15/oe3/RESULTADOS_OE3.md). Esas tablas se proponen como resultados oficiales nuevos de OE3; las tablas anteriores quedan como antecedentes históricos. Se conservan el E6 operativo y el calibrador. [Procedencia y figuras 6.1–6.2](evidencias/pi15/trazabilidad/INFORME_T10_T11.md).
