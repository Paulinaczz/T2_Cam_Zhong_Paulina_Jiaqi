# Informe técnico para la tesis, PI13 y PI14

Este informe consolida la validación técnica de PDS-QA y registra la decisión final de excluir CP10. Las pruebas y mediciones se realizaron en fases anteriores. Los enlaces apuntan a las salidas originales para mantener trazabilidad.

| Resultado | Evidencia disponible | Alcance para la tesis |
|---|---|---|
| O1 y CP01 | 18 módulos y 21 métricas validados. Se verificaron el orden por margen SVM, la comparación experimental de probabilidad calibrada dividida por max(LOC, 1) y ManualUp por coste ascendente. El CSV comparativo contiene las 18 filas. | Validación funcional sobre datos de ejemplo. [CSV comparativo](../../evidencias/pi13/o1_20261115_181721/CP01_comparacion.csv) |
| CP05 | SQLite conservó una ejecución completa con UUID y huellas, junto con 18 predicciones verificadas. | Trazabilidad local de una ejecución. [Registro de CP01 y CP05](../../evidencias/pi13/o1_20261115_181721/CP01_CP05.json) |
| Pruebas automatizadas | 16 pruebas pytest aprobadas, incluida la regresión de UI04 que contrasta con el CSV experimental. Las 15 pruebas del registro de O1 corresponden a una versión anterior. | Verificación del código y los casos cubiertos. [Registro final](../../evidencias/pi14_cierre/verificacion.txt) |
| Casos negativos | CP02 rechazó la falta de LOC. CP03 rechazó infinito y texto. CP04 escapó con un apóstrofo el identificador de prueba al exportar. CP11 rechazó identificadores duplicados y XLSX. CP12 bloqueó el inicio por hash usando una copia alterada aislada. | Verificación de los casos concretos y sus salidas. [Capturas reales y resultados](../../evidencias/pi14_revision/C/LEEME.md) |
| CP06 al límite | 30 repeticiones con 20 000 módulos sintéticos y 2,12 MiB. p95 **67,837039 s** y mediana **64,824879 s**. | Lector hasta 20 000 filas y 10 MiB. Ensayo en Windows 10, Ryzen 5 3600 y unos 16 GiB de RAM con 18 perfiles repetidos. El total comparativo incluye lectura y validación, inferencia comparativa, calibración, rankings y serialización. Excluye arranque, espera de servidor, persistencia, inferencia adicional del ranking operativo, transferencia y renderizado. No había meta temporal para este lote. [Mediciones y protocolo](../../evidencias/pi14_cierre/escalabilidad/LEEME.md) |
| CP09 | Dos repeticiones locales con semilla 42 produjeron CSV idénticos. NumPy 2.1.3 reprodujo F1, AUC-ROC y AP de 4 de 15 recetas históricas, frente a 3 de 15 con la versión base. | **Parcialmente comprobado.** Los controles encontraron sensibilidad del escalado y de los vecinos usados por ADASYN. Cambiar el paquete NumPy también cambió su OpenBLAS. No se recuperó el entorno completo ni las trazas intermedias de Colab, por lo que sigue abierta la atribución histórica exacta. PI15 completó las 27 configuraciones y 675 ajustes candidatos. La reproducción exacta del entorno histórico sigue parcialmente comprobada. [Diagnóstico y trazas](../../evidencias/pi14_cierre/CP09/LEEME.md) |
| O7 / CP10 | **NO EJECUTADO** por decisión de alcance. | Sin evidencia empírica de satisfacción, facilidad de uso, errores de interacción ni tiempo humano de QA. Se registra como limitación. [Matriz actualizada](../../evidencias/pi14_cierre/INFORME.md) |

La evaluación exploratoria por proyecto registró Recall@20 % LOC medio de 29,09 % para probabilidad calibrada por LOC y 28,74 % para ManualUp. CM1 y JM1 fueron favorables a la estrategia calibrada. Los intervalos bootstrap por proyecto incluyeron cero. Los resultados no sustentan superioridad consistente frente a ManualUp. LOC aproxima el tamaño de los módulos revisados y no permite inferir ahorro de minutos de trabajo. [Resultados por proyecto](../../research/experimentos/estrategia_esfuerzo/principal_deduplicada/diferencias_20pct_LOC_por_proyecto.csv)

## Texto listo para adaptar

**Tesis · Limitaciones.** «La evaluación de usabilidad con participantes (CP10) no se ejecutó por decisión de alcance. Por ello, el estudio no aporta evidencia empírica sobre satisfacción, facilidad de uso o cambios en el tiempo humano de aseguramiento de calidad. Las mediciones de rendimiento describen el tiempo de procesamiento del flujo comparativo en el entorno evaluado. El presupuesto en LOC se utilizó como aproximación del esfuerzo de revisión».

**PI13 · Evidencias.** «La validación del prototipo verificó la carga de un CSV de 18 módulos con 21 métricas, los tres rankings y la conservación de la ejecución y sus predicciones en SQLite. La suite de 16 pruebas aprobó en la versión revisada. Las capturas de CP02, CP03, CP04, CP11 y CP12 documentan los comportamientos observados. CP10 se registra como NO EJECUTADO».

**PI14 · Resultados y discusión.** «En 30 corridas con 20 000 módulos sintéticos, el flujo comparativo registró una mediana de 64,824879 s y un p95 de 67,837039 s. El total corresponde al procesamiento del servicio bajo las condiciones documentadas. CP09 comprobó repetibilidad local a semilla fija para las recetas ensayadas. La reproducción histórica fue parcial y la nueva búsqueda completa ya se ejecutó con 27 configuraciones y 675 ajustes candidatos».

## Material complementario

- [Guion narrado para una demostración de 6 min 40 s](GUION_VIDEO.md)
- [Decisiones académicas para revisar con el profesor](APROBACIONES_PROFESOR.md)
