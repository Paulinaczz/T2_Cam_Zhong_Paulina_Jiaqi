# Notas de v1.0-tesis

Versión del prototipo PDS-QA preparada para la tesis. Incluye E6 operativo, calibrador verificado, ranking SVM, comparación calibrada/LOC y ManualUp, exportación y trazabilidad SQLite.

- Evidencias funcionales y negativas, corrección de UI04 y suite de 16 pruebas.
- Rendimiento documentado en 30 corridas con 20 000 módulos sintéticos, p95 comparativo de 67,837039 s. El alcance y exclusiones se detallan en evidencias/pi14_cierre/escalabilidad.
- Búsqueda Nested LOPO completa de PI15 con 27 configuraciones, cinco proyectos externos, selección global, semilla 42 y entorno de investigación fijado. Las métricas externas nuevas de OE3 y su comparación con Colab están en evidencias/pi15/oe3.
- E6 y el calibrador originales conservan sus huellas. El candidato reentrenado de la búsqueda nueva queda separado en la carpeta experimental.
- CP09 histórico sigue parcialmente comprobado: el entorno original de Colab no se recuperó por completo. La corrida nueva completa regenera los resultados de OE3 en el entorno documentado.
- CP10 NO EJECUTADO por decisión de alcance. Sin evidencia empírica de satisfacción, facilidad de uso ni ahorro de tiempo humano.
- T10 documenta los hashes de las copias y las fuentes de referencia con la limitación de procedencia. T11 identifica los CSV y el generador exacto de las figuras 6.1 y 6.2 de la tesis.
- Video narrado y correcciones finales de redacción de la tesis continúan pendientes.

El ZIP de la versión incluye las evidencias de O1, PI13–PI14 y PI15 y la comprobación posterior de main. Las bases SQLite privadas y los archivos temporales quedan fuera del paquete.
