# Evidencia visual del prototipo PDS-QA — 10/11/2026

Se adjuntan **11 capturas originales sin editar**: 8 de Streamlit (UI01–UI06) y 3 de CSV abiertos en Excel.

- Respaldo visual positivo: CP01 (carga, validación, predicción, ranking, exportación) y CP05 (historial).
- CP04: captura de exportación ordinaria; el rechazo/saneamiento de una fórmula `=1+2` solo está demostrado por el reporte automático en `validacion_local.zip`.
- CP02, CP03 y CP11: no hay capturas del mensaje de rechazo en la interfaz; sí existen logs backend previos.
- CP12: se observa la identificación del modelo y su SHA; no hay captura de una comprobación fallida de hash, cuya evidencia es backend.
- CP06: p95 y repeticiones provienen del CSV de tiempos del ZIP local; no se infieren de capturas de pantalla.
- CP10: no se ha realizado un estudio con participantes reales.
- La captura de Excel en una sola columna es compatible con un problema de delimitador/región de Excel; importar con **Datos > Desde texto/CSV**, delimitador **coma**. No se concluye que el CSV tenga un defecto.
- Los archivos muestran hora local del 10/11/2026; las pruebas automatizadas ocurrieron el 09/11/2026 (hora Perú), por lo que esto es una **adenda posterior**, no evidencia de capturas anexadas el día anterior.

Consultar `INDICE_CAPTURAS.csv` para el nombre de archivo, asociación al CP y limitaciones de cada captura. Los SHA-256 permiten verificar que las copias coinciden con lo recibido.
