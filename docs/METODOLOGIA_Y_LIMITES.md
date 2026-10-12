# Criterios científicos y límites del prototipo

- **DSR**: marco de investigación y construcción/evaluación del artefacto.
- **CRISP-DM**: seis fases del trabajo de datos y Machine Learning.
- **CPDP**: escenario de predicción entre proyectos; no sustituye a CRISP-DM.
- **Validación anidada Leave-One-Project-Out**: cada proyecto se reserva íntegramente para una evaluación externa; dentro de las fuentes se elige configuración sin mirar la etiqueta del proyecto objetivo.
- **Modelo final**: el algoritmo y escenario seleccionados por CV entre proyectos se ajustan posteriormente sobre los cinco proyectos históricos.

El F1 CV `0.39725` se refiere a la evaluación de configuraciones reentrenadas durante la validación entre proyectos, NO al rendimiento medido sobre un nuevo sexto proyecto para el `.joblib` definitivo.

La diferencia F1 entre los mejores candidatos es estrecha. Debe analizarse estabilidad/repeticiones para afirmar superioridad estadística. La comparación de priorización a 10 % de módulos frente a LOC en la validación externa no demostró superioridad consistente de ML; por tanto la contribución demostrada actualmente es una herramienta funcional de clasificación, ranking y trazabilidad con rendimiento predictivo limitado a los proyectos evaluados.

Pendiente: (a) verificación documental de orígenes NASA/PROMISE; (b) definición y equivalencia de columnas/etiquetas, en especial `lOCodeAndComment`; (c) evaluación de datos no vistos de organizaciones reales con métricas homogéneas; (d) pruebas de usabilidad con analistas SQA; (e) respaldo y políticas de retención de la base de datos; (f) análisis estadístico de diferencias entre algoritmos.

El prototipo no extrae métricas desde repositorios ni determina certeza, tipo o severidad de un defecto. En operaciones reales, una puntuación ordena prioridades sugeridas y **no reemplaza al juicio del equipo de QA**.
