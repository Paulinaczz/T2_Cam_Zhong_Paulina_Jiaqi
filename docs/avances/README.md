# Entregables y Avances Formales de Validación (PI13 y PI14)

Este directorio reúne las versiones más recientes de los informes de validación técnica y operativa del proyecto de tesis **PDS-QA**, correspondientes a los entregables **PI13** y **PI14**.

## Documentos Disponibles

- [T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf](T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf) / [.docx](T2_PI13_CON_EVIDENCIAS_VISUALES_10NOV2026.docx): Informe de ejecución de pruebas técnicas y de seguridad (CP01–CP06, CP11–CP12), mediciones de tiempo y adenda con respaldo fotográfico de la interfaz.
- [T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf](T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.pdf) / [.docx](T2_PI14_CON_EVIDENCIAS_VISUALES_10NOV2026.docx): Informe de consolidación de resultados, análisis descriptivo de metas, matriz de trazabilidad y estado de cumplimiento.
- [T2_ADENDA_CAPTURAS_RESUMEN_10NOV2026.md](T2_ADENDA_CAPTURAS_RESUMEN_10NOV2026.md): Resumen de la adenda visual con las 11 capturas incorporadas el 10 de noviembre de 2026.

## Estado de Ejecución de Casos de Prueba (PI11–PI12 a PI13–PI14)

| Caso | Tipo | Estado Actual | Evidencia Asociada |
| :--- | :--- | :--- | :--- |
| **CP01** | Funcional (Carga y ranking 18 módulos) | **Aprobado** (Backend + UI) | `evidencias/pi13/validacion_local/casos/CP01/` y capturas `EVV01`–`EVV06` |
| **CP02** | Seguridad (Rechazo sin columna `loc`) | **Aprobado en backend** | `evidencias/pi13/validacion_local/casos/CP02/rechazo.txt` |
| **CP03** | Seguridad (Rechazo de Inf y no numéricos) | **Aprobado en backend** | `evidencias/pi13/validacion_local/casos/CP03/rechazos.txt` |
| **CP04** | Seguridad (Escapado de fórmulas CSV) | **Aprobado en backend** | `evidencias/pi13/validacion_local/casos/CP04/salida_sanitizada.csv` |
| **CP05** | Funcional (Persistencia e historial SQLite) | **Aprobado** (Backend + UI) | `evidencias/pi13/validacion_local/casos/CP05/` y captura `EVV07` |
| **CP06** | Rendimiento (30 repeticiones 18 filas y JM1) | **Medición ejecutada** ($p_{95}=0,0767\text{ s} \le 5\text{ s}$) | `evidencias/pi13/validacion_local/casos/CP06/resumen_cp06.csv` |
| **CP07** | Experimental (Calidad predictiva) | **Documentado en investigación** | `research/experimentos/` |
| **CP08** | Experimental (Comparación configuraciones) | **Documentado en investigación** | `research/experimentos/comparacion_configuraciones/` |
| **CP09** | Experimental (Sensibilidad/Replicabilidad) | **Búsqueda nueva completa; reproducción histórica parcial** | En evaluación metodológica |
| **CP10** | Usabilidad / aceptación | **NO EJECUTADO** | Fuera del alcance final. Sin evidencia de usabilidad |
| **CP11** | Seguridad (Extensión y duplicados) | **Aprobado en backend** | `evidencias/pi13/validacion_local/casos/CP11/rechazos.txt` |
| **CP12** | Seguridad (Integridad SHA-256 del modelo) | **Aprobado en backend** | `evidencias/pi13/validacion_local/casos/CP12/rechazo_hash.txt` |

## Elementos Mantenidos Explícitamente como Pendientes

1. **CP09:** La repetición de recetas externas está registrada. La búsqueda nueva completó 27 configuraciones y 675 ajustes candidatos. La recuperación exacta del entorno histórico sigue parcial.
2. **CP10:** NO EJECUTADO por decisión de alcance. Se registra como limitación del estudio.
3. **Capturas de rechazo de interfaz:** Se registraron capturas reales para CP02, CP03, CP04, CP11 y CP12 en la [revisión PI13–PI14](../../evidencias/pi14_revision/C/LEEME.md).
4. **Observaciones del asesor:** Las observaciones metodológicas permanecen bajo revisión continua hasta contar con la confirmación y aprobación formal correspondiente.
