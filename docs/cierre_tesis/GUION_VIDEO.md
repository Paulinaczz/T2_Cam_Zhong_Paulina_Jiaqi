# Guion narrado de demostración de PDS-QA

Duración estimada: **6 min 40 s**. Grabar en un perfil local de prueba con el CSV de ejemplo que acompaña al repositorio. Abrir Streamlit desde la raíz con el entorno del proyecto. Para que el historial de la grabación solo muestre datos de demostración, usar una ruta nueva y desechable mediante la variable PDS_DB_PATH. Registrar el UUID que produzca la sesión. Las capturas anteriores se pueden mostrar como evidencia identificada de su propia ejecución.

| Tiempo | Pantalla y acción | Narración |
|---|---|---|
| 0:00–0:40 | UI01. Mostrar el nombre, E6 y el aviso del modelo local verificado. | «PDS-QA recibe métricas estáticas precalculadas de módulos de software. El prototipo estima propensión a defectos y ayuda a ordenar qué módulos revisar. La clasificación orienta la revisión y requiere comprobación posterior». |
| 0:40–1:30 | UI02. Cargar data/sample/ejemplo_carga.csv y pulsar **Validar archivo**. En UI03 mostrar 18 módulos, 21 métricas y la huella de entrada. | «El archivo de ejemplo contiene 18 módulos. La validación comprueba las 21 métricas obligatorias y los identificadores. La huella SHA-256 permite identificar exactamente el CSV utilizado en esta ejecución». |
| 1:30–2:25 | En UI03 pulsar **Ejecutar predicción y guardar evidencia**. En UI04 abrir **Ranking Operativo**. Mostrar clase, margen y prioridad. | «E6 es un SVM. La prioridad operativa sigue el margen de decisión en orden descendente. El margen es un score de ordenación. La clase representa una propensión estimada y no confirma que haya un defecto». |
| 2:25–3:40 | En UI04 abrir **Comparación de Estrategias**. Ampliar la matriz y mostrar las tres columnas de prioridad. Pulsar **Exportar comparación de estrategias (CSV)**. | «Aquí se comparan el margen SVM, la probabilidad calibrada dividida por el coste LOC y ManualUp, que prioriza módulos pequeños. La densidad se presenta como estrategia experimental. En el estudio por proyecto, CM1 y JM1 favorecieron la estrategia calibrada. La evidencia no sustenta una superioridad consistente frente a ManualUp». |
| 3:40–4:35 | UI05. Abrir el historial y elegir el UUID generado en la grabación. Mostrar estado, filas y huellas. | «SQLite conserva la ejecución y sus 18 predicciones asociadas. El historial permite consultar el UUID, la huella del CSV y la del modelo. Estas referencias permiten comparar la consulta con el archivo usado y la versión del artefacto». |
| 4:35–5:25 | Mostrar la captura archivada de CP02 y la de CP12. Mostrar la fila escapada en la salida publicada de CP04, como texto. Identificar cada evidencia como archivada. | «Se verificó el rechazo de entradas inválidas. En esta captura falta la columna LOC. También se comprobó el escapado de un identificador en la exportación y el bloqueo de arranque por una huella de modelo incompatible. La prueba de integridad alteró una copia aislada». |
| 5:25–6:40 | Mostrar el resumen CP06 y la matriz final. Identificar en la diapositiva que los datos son sintéticos. | «Se aprobaron 16 pruebas automatizadas. En 30 corridas con 20 000 módulos sintéticos, el flujo comparativo registró un p95 de 67,837039 segundos. Este tiempo corresponde a la validación, comparación y exportación del servicio. Excluye arranque, persistencia, espera del servidor, inferencia adicional, transferencia y renderizado. CP09 quedó parcialmente comprobado y CP10 no se ejecutó. Por tanto, esta demostración documenta el funcionamiento y sus límites técnicos». |

## Evidencias para insertar en edición

- [Capturas archivadas de UI03, UI04 y UI05](../../evidencias/pi13/o1_20261115_181721/capturas/). Si se muestran las capturas antiguas de la comparación, usar la vista de la matriz o identificar la versión. La grabación actual debe mostrar el rótulo corregido CM1 y JM1.
- [CP02, CP04 y CP12](../../evidencias/pi14_revision/C/LEEME.md).
- [Resumen CP06 para la lámina final](../../evidencias/pi14_cierre/escalabilidad/ensayo_20000/resumen.json).
- [Matriz final de observaciones](../../evidencias/pi14_cierre/INFORME.md).

Antes de grabar, ocultar rutas locales y otros datos del escritorio. Para enseñar el historial, usar únicamente las ejecuciones del CSV de demostración. Mantener las cifras de las pruebas tal como se registraron.
