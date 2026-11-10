# Adenda visual — PI13 y PI14 — 10 de noviembre de 2026

**Evidencia recibida:** 8 capturas de Streamlit (UI01 a UI06) y 3 de CSV abiertos en Excel, con índice SHA-256.

**Conclusión verificada:** la interfaz muestra el recorrido positivo de importación de un CSV de 18 filas, verificación de 21 métricas, predicción E6 con dos módulos positivos, ranking/exportación e historial de ejecución COMPLETADA en SQLite. No representa validación con usuarios, precisión predictiva ni confirmación de defectos reales.

**Cobertura:**
- CP01: evidencia UI positiva recibida (UI02–UI04, ejemplo y CSV exportado) y logs/backend previos.
- CP05: evidencia UI positiva de historia, UUID, 18 módulos, 2 clasificados con riesgo, estado COMPLETADA.
- CP04: backend evidencia sanitización de ID de fórmula; captura nueva muestra exportación normal pero no un caso malicioso.
- CP02, CP03 y CP11: continúan sin capturas de los mensajes de rechazo en UI; logs/backend previos disponibles.
- CP12: backend acreditó bloqueo por hash alterado; screenshots exhiben estado/modelo SHA, no pantalla de bloqueo.
- CP06: 60 mediciones de rendimiento en ZIP, no visibles en nuevas capturas.
- CP10: sin participantes ni cuestionario I-05 validado.

**Fecha:** archivos de captura de la mañana del 10/11/2026, **posteriores** a la ejecución automática local del 09/11/2026. Debe figurar como adenda; no se atribuye al envío anterior.

**Excel:** las capturas muestran el CSV como cadenas separadas por comas dentro de la columna A. Esto por sí solo no demuestra un defecto del CSV; para visualizarlo en columnas, importarlo como texto/CSV indicando separador coma.

**Limitación científica invariable:** el análisis E6 probabilidad/LOC fue 29,09 % vs. ManualUp 28,74 % en Recall@20 % LOC, pero el ML gana en 2/5 proyectos y no demuestra superioridad consistente.

Los PDF/Word actualizados contienen la adenda visual; las 11 imágenes originales y sus hashes están en `capturas_originales/` y `INDICE_CAPTURAS.csv`.
