# Evidencias operativas O1 del PR 3

Validación de la rama `feature/observacion-o1-estrategia-calibrada` en el commit `18108025d5108d6f73bcd98bf465e5d494a58c77`. Se usó Windows con Python 3.13. El flujo de GitHub Actions usa Python 3.12.

- [CP01, ranking operativo](CP01_ranking.csv) y [matriz de los tres rankings](CP01_comparacion.csv). Se validaron 18 módulos con 21 métricas.
- [CP01 y CP05, comprobaciones y metadatos de ejecución](CP01_CP05.json) y [predicciones recuperadas de SQLite](CP05_predicciones.csv).
- [CP06, 60 mediciones nuevas](CP06_mediciones.csv), [resumen estadístico](CP06_resumen_segundos.csv) y [huellas de JM1](CP06_procedencia_JM1.json).
- [Verificación de E6 y calibrador](integridad.json) y [registro de las 15 pruebas aprobadas](suite_pytest.txt). Se ocultó la ruta privada del registro original. La repetición de la suite para preparar la publicación también pasó las 15 pruebas.
- [Ejecución de navegador](UI_navegador.json) y [comprobación con AppTest](UI_streamlit.json). Son ejecuciones independientes de la comprobación de servicio de CP05.

## CP06

Se realizaron 30 repeticiones independientes con 18 módulos y 30 con JM1 completo (13 204 módulos). El p95 del total comparativo fue **0,096739 s** y **47,783318 s**, respectivamente. La meta de 5 s corresponde al lote de 18 módulos.

Los tiempos están en segundos. Se leyeron los CSV a memoria antes del bucle. La validación incluye el parseo. La inferencia suma las llamadas a `predict` y `decision_function` de la comparación. Los rankings incluyen el cálculo de posiciones y la construcción de la tabla, con la sobrecarga de instrumentación. La exportación mide la serialización a bytes. El total excluye arranque, persistencia, inferencia adicional en UI04 y renderizado. El p95 se calculó por fase con interpolación lineal y se informa la desviación estándar muestral.

Los finales CRLF de JM1 se normalizaron a LF en memoria y el SHA-256 resultante coincidió con el de procedencia. Se verificó Streamlit en paralelo durante parte de las mediciones de JM1. CP06 caracteriza el rendimiento del prototipo en el equipo de prueba. Los resultados científicos frente a ManualUp provienen de Nested LOPO.

## Capturas reales de Streamlit

- [UI03 · Validación de 18 módulos](capturas/UI03_validacion.jpg)
- [UI04 · Ranking SVM](capturas/UI04_ranking_svm.jpg)
- [UI04 · Comparación de estrategias](capturas/UI04_comparacion.jpg)
- [UI04 · Matriz y botón de exportación](capturas/UI04_matriz.jpg)
- [UI04 · Matriz ampliada con los tres rankings](capturas/UI04_matriz_ampliada.jpg)
- [UI05 · Ejecución y hashes en el historial](capturas/UI05_historial.jpg)
