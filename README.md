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
4. **UI04 (Inferencia y Priorización):** Ejecuta la predicción mediante el clasificador SVM, asigna la prioridad según el margen funcional decreciente y permite exportar el ranking sanitizado en CSV.
5. **UI05 (Historial y Trazabilidad):** Consulta el registro auditable persistido en base de datos SQLite aislada (identificador UUID, marcas de tiempo UTC, hashes y estado de ejecución).
6. **UI06 (Guía y Limitaciones):** Explica el significado del margen de soporte y advierte que el valor numérico no es una probabilidad porcentual.

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

> **Conclusión metodológica:** La diferencia media en Recall@20 % LOC es de +0,36 puntos porcentuales y los intervalos bootstrap al 95 % de las diferencias incluyen el cero en la totalidad de los proyectos. Por lo tanto, **no existe evidencia estadística suficiente para sostener una superioridad consistente del aprendizaje automático frente a la regla determinista de priorizar módulos pequeños (ManualUp)**. Estos resultados forman parte del análisis experimental de investigación y se documentan con rigurosidad académica en [docs/METODOLOGIA_Y_LIMITES.md](file:///docs/METODOLOGIA_Y_LIMITES.md).

---

## 4. Evidencias de Validación Técnica y Operativa (PI13–PI14)

Los informes formales se encuentran disponibles en:
- [T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf](file:///docs/avances/T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf) / [.docx](file:///docs/avances/T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.docx)
- [T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf](file:///docs/avances/T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf) / [.docx](file:///docs/avances/T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.docx)
- [T2_ADENDA_CAPTURAS_RESUMEN_10NOV2026.md](file:///docs/avances/T2_ADENDA_CAPTURAS_RESUMEN_10NOV2026.md)

### Resumen de Pruebas Ejecutadas

| Caso | Tipo | Resultado Técnico Obtenido | Archivos de Respaldo |
| :--- | :--- | :--- | :--- |
| **CP01** | Funcional | Importación, validación, inferencia y ordenación exitosa de 18 módulos | `evidencias/pi13/validacion_local/casos/CP01/` |
| **CP02** | Seguridad | Rechazo inmediato de CSV sin columna `loc`; SQLite inalterada | `evidencias/pi13/validacion_local/casos/CP02/` |
| **CP03** | Seguridad | Rechazo controlado de valores infinitos (`inf`) y datos alfanuméricos | `evidencias/pi13/validacion_local/casos/CP03/` |
| **CP04** | Seguridad | Escapado de fórmulas CSV (`=1+2` sanitizado a `'=1+2`) | `evidencias/pi13/validacion_local/casos/CP04/` |
| **CP05** | Funcional | Generación de UUID, verificación de hashes y persistencia de 18 registros | `evidencias/pi13/validacion_local/casos/CP05/` |
| **CP06** | Rendimiento | 30 repeticiones lote 18: $p_{95} = \mathbf{0,0767\text{ s}}$ (meta $\le 5\text{ s}$ superada). 30 repeticiones JM1: $p_{95} \approx \mathbf{50,50\text{ s}}$ | `evidencias/pi13/validacion_local/casos/CP06/` |
| **CP11** | Seguridad | Rechazo de extensiones incompatibles (`.xlsx`) e IDs duplicados | `evidencias/pi13/validacion_local/casos/CP11/` |
| **CP12** | Seguridad | Bloqueo estricto del pipeline ante alteración del hash SHA-256 | `evidencias/pi13/validacion_local/casos/CP12/` |
| **Pytest** | Automatizada | **14 pruebas aprobadas al 100 %** (0 fallos, 0 omisiones) | `evidencias/pi13/validacion_local/suite_pytest.txt` |

Las evidencias visuales con las 11 capturas de pantalla de la interfaz y su matriz de trazabilidad se ubican en [evidencias/pi13/capturas/INDICE_CAPTURAS.csv](file:///evidencias/pi13/capturas/INDICE_CAPTURAS.csv).

---

## 5. Casos y Observaciones Mantenidos como Pendientes

En estricto cumplimiento del código de ética académica y las directrices de asesoría:
1. **CP09 (Evaluación formal de repetibilidad):** Permanece como pendiente hasta culminar la serie requerida de repeticiones de modelado.
2. **CP10 (Validación con usuarios en entorno real):** Requiere la aplicación del instrumento de evaluación I-05 a evaluadores y desarrolladores humanos en sesiones controladas; no se formulan estimaciones simuladas.
3. **Capturas de rechazo visual en navegador:** Las pantallas de alerta de error específicas de CP02, CP03 y CP11 en la interfaz no disponen de captura fotográfica en esta entrega, quedando su efectividad demostrada a nivel de backend y logs.
4. **Observaciones metodológicas del asesor:** En proceso de sustentación continua hasta contar con el dictamen formal.

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
