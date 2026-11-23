# Informe breve de cierre PI15

## Versión del artefacto

El usuario autorizó la publicación del cierre documental, la fusión del PR #3 y la creación de v1.0-tesis después de validar main. La versión identificada por esa etiqueta conserva E6 y su calibrador y recoge los tres rankings, las evidencias técnicas, CP10 NO EJECUTADO y los documentos de cierre. Las comprobaciones posteriores de main y los enlaces definitivos se adjuntan al release. [Plan y alcance](version_final/PLAN_FUSION.md) · [Notas de versión](version_final/NOTAS_RELEASE.md)

## OE3 regenerado

La búsqueda completa terminó con seis checkpoints de 27 candidatos y 675 ajustes candidatos verificados sin errores. Se generaron tablas por proyecto y por algoritmo, promedios macro, selección global, candidato experimental, logs, versiones y SHA-256 de salidas. El candidato global nuevo es XGBoost/E5_SMOTE_MI y está separado de E6.

| Algoritmo | F1 macro nuevo | AUC-ROC macro nuevo | AP macro nueva |
|---|---:|---:|---:|
| XGBoost | 0,423066 | 0,711975 | 0,380567 |
| SVM | 0,413096 | 0,727687 | 0,348831 |
| Random Forest | 0,361601 | 0,693271 | 0,360133 |

Para la Tabla 6.1 y OE3 se recomiendan los nuevos resultados de esta ejecución completa y su entorno fijado. Las cifras históricas se conservan como antecedente. El orden por F1 ahora favorece XGBoost. El experimento de OE4 frente a ManualUp permanece independiente y conserva sus cifras. CP09 ya incluye una ejecución anidada completa en el entorno nuevo, pero la recuperación exacta del entorno histórico y la repetición completa adicional siguen sin comprobarse. [Resultados y contraste](oe3/RESULTADOS_OE3.md) · [Completitud](oe3/validacion_completitud.json)

## T10 y T11

- T10. Los cinco archivos se identificaron por URL de espejo fijada a commit, último commit de archivo y SHA-256. Coinciden con las copias locales y el manifiesto del experimento. La copia JM1 usada tiene 13 204 filas frente a las 10 885 de la ficha consultada en Tera-PROMISE. Se mantiene explícita la limitación de equivalencia y procedencia y se cita Shepperd et al. (2013).
- T11. Las imágenes de las figuras 6.1 y 6.2 del DOCX recibido coinciden exactamente con los PNG del repositorio al convertirlos a escala de grises. Se identificaron sus CSV y las líneas 226 y 239 de la función ejecutar en cpdp_estrategia_esfuerzo.py. Se prepararon las fuentes precisas para las leyendas.

[Informe y fuentes](trazabilidad/INFORME_T10_T11.md) · [Prueba de correspondencia](trazabilidad/figuras_tesis_verificadas.json)

## Pendientes del documento académico

Los DOCX recibidos se mantuvieron intactos. Quedan por incorporar las leyendas y las tablas oficiales nuevas en la tesis. La revisión PI15 también requiere depurar lenguaje de proceso y anexos del curso, alinear PE1–PE4 y OE1–OE4, completar estructura e índices, reorganizar el capítulo VI, unificar las mediciones oficiales y redondear tiempos del resumen y conclusiones. El video tiene guion preparado y sigue sin grabarse. La coherencia del contraste unilateral de OE4 señalada en la sección 5.2 de PI15 debe resolverse en la redacción y reporte estadístico de la tesis. No se modificaron estadísticas históricas ni el título registrado.

La formalización de OE2, la interpretación descriptiva de los criterios OE1–OE3, el tratamiento de CP10 y la conservación del título siguen sujetos a la sesión académica indicada por el profesor.
