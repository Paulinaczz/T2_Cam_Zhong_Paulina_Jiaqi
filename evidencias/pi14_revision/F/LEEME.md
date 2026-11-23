# Informe de consolidación PI13–PI14

Revisión sobre feature/observacion-o1-estrategia-calibrada con base c6536fc. El alcance de esta fase deja separadas las comprobaciones de reproducibilidad, los instrumentos para personas y los ensayos operativos.

| Bloque | Estado técnico | Entregables y decisiones |
|---|---|---|
| A · CP09 | Repetición controlada de recetas externas ejecutada. CP09 completo pendiente | [Protocolo, comandos y resultados](../A/LEEME.md). La serie completa de búsqueda interna requiere más de 2 000 ajustes candidatos para tres repeticiones. Su ejecución requiere reservar tiempo de cómputo |
| B · CP10 | **NO EJECUTADO** por decisión de alcance final | Instrumentos preparados en aquella fase, conservados como borradores históricos. Sin evidencia de usabilidad |
| C · Streamlit | CP02, CP03, CP04, CP11 y CP12 ejecutados | [Capturas y salidas](../C/LEEME.md). Se comprobó el rechazo, escapado CSV y bloqueo por integridad con ejecución y modelo aislados |
| D · OE1–OE3 | Auditoría y tabla completadas | [Criterios y tabla](../D/criterios_y_metricas.md). Se requiere aprobación para la redacción oficial de OE2 y cualquier criterio nuevo de calidad |
| E · Escalabilidad y OE4 | Límites comprobados y alcance documentado | [Notas y prueba de límites](../E/escalabilidad_y_OE4.md). Las metas para lotes grandes y el protocolo extremo a extremo son propuestas |
| F · Consolidación | Documentación técnica actualizada y paquete separado de O1 | Documentación técnica, corrección de UI04, prueba de regresión, evidencias/pi14_revision y ZIP general |

## Hallazgos y pendientes

- La copia disponible de PI11–PI12 remite a I-05 e I-06, pero solo adjunta anexos hasta I-03. Los instrumentos que se prepararon en esa fase se conservan como borradores históricos. CP10 quedó fuera del alcance final.
- Se corrigió el rótulo de UI04: CM1 y JM1, tal como indica el CSV experimental. Los resultados, artefactos y capturas originales de O1 conservan su versión. [Prueba de regresión](../UI04/LEEME.md)
- La revisión del profesor también menciona el video narrado de 5–8 minutos. El guion está preparado y la grabación queda pendiente. [Guion](../../../docs/cierre_tesis/GUION_VIDEO.md)
- Las tablas de OE1–OE3 proceden de resultados históricos Nested LOPO, mientras que las series de A y las evidencias de C son nuevas. Los formatos de B están vacíos de valoraciones y respuestas.

## Verificación final local

[Salida de pytest y control de diferencias](verificacion_final.txt).

## Estado por observación del profesor

| Observación | Estado |
|---|---|
| O1 · Priorización consciente del esfuerzo | Implementada, probada y corregida en UI04. Evidencias previas conservadas. El estudio exploratorio no demuestra superioridad consistente frente a ManualUp |
| O2 · Decisión estadística con cinco pares | Documentada la limitación de Wilcoxon, los deltas e intervalos por proyecto y el alcance descriptivo. Cierre académico sujeto al asesor |
| O3 · Cohortes, grupos conflictivos y fuentes | Reglas y huellas verificadas. La certificación documental de procedencia sigue pendiente |
| O4 · Redacción OE2 | Propuesta Nested LOPO trazada al protocolo. Aprobación del cambio formal pendiente |
| O5 · Criterios OE1/OE3 y métricas predictivas | Tabla externa y auditoría terminadas. Los criterios nuevos requieren aprobación previa |
| O6 · Rendimiento | Ejecutadas 30 corridas por lote para 18 y 13 204 módulos. La prueba de lectura a 20 000 no mide latencia |
| O7 · Usabilidad | **CP10 NO EJECUTADO**. Piloto fuera del alcance final y sin evidencia de usabilidad |
| O8 · Extracción de métricas | Limitación documentada: se reciben métricas precomputadas. No se ejecutó una demostración de extracción |
| O9 · Organización y calendario | Evidencias separadas. El piloto CP10 quedó fuera del alcance final |
| CP09 · Repetibilidad | Local comprobada a receta fija. [Discrepancia histórica](../A/diagnostico_discrepancia.md) y búsqueda completa pendientes |
