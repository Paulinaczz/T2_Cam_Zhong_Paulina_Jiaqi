# Informe de cierre técnico PI13–PI14

Rama feature/observacion-o1-estrategia-calibrada, con bd9b554 como base de esta fase. Las evidencias se mantienen separadas de O1. Se conservaron E6, el calibrador y las tablas experimentales históricas.

## Comprobado

| Observación | Evidencia |
|---|---|
| O1 · Priorización y UI04 | Evidencias de O1 publicadas. La comparación operativa y la corrección CM1/JM1 se conservan. El estudio exploratorio no apoya superioridad consistente. [O1](../pi13/o1_20261115_181721/LEEME.md) |
| O2 · Estadística con cinco proyectos | Limitación del contraste exacto bilateral y alcance de deltas e intervalos descriptivos documentados. El dictamen académico corresponde al asesor. [Hipótesis y OE4](../pi14_revision/E/escalabilidad_y_OE4.md) |
| O6 · Rendimiento | El lector admite 20 000 filas y 10 MiB. Se midieron 30 corridas con 20 000 módulos sintéticos (2,12 MiB), con **p95 67,837039 s** y **mediana 64,824879 s**. El total corresponde al flujo comparativo de servicio. El plan no fijó una meta para ese lote. [Resultados y exclusiones](escalabilidad/LEEME.md) |
| Suite automatizada | **16 pruebas pytest aprobadas**, incluida la prueba que compara el texto de UI04 con el CSV experimental. [Verificación](verificacion.txt) |
| Casos negativos | CP02, CP03, CP04, CP11 y CP12 conservan sus capturas reales y salidas de la revisión anterior. [Evidencias](../pi14_revision/C/LEEME.md) |

## Parcialmente comprobado

| Observación | Comprobado | Pendiente |
|---|---|---|
| CP09 · Repetibilidad | Dos repeticiones locales con semilla 42 produjeron CSV idénticos. Se observó sensibilidad del escalado y ADASYN a componentes numéricos. NumPy 2.1.3 reprodujo las tres métricas históricas de 4 de 15 recetas. [Diagnóstico](CP09/LEEME.md) | Recuperar el entorno completo y las trazas intermedias de Colab para identificar la primera divergencia histórica. Repetir Nested LOPO con 27 configuraciones. |
| O3 · Cohortes y fuentes | Cinco hashes, política de deduplicación sin etiqueta, sensibilidad de grupos conflictivos y pliegues verificados. [Diagnóstico](CP09/LEEME.md) | Procedencia documental y disponibilidad de pares de fuente y métricas de referencia. |
| O4 · OE2 | Protocolo Nested LOPO respaldado por el código y las particiones. [Auditoría](../pi14_revision/D/criterios_y_metricas.md) | Aprobación de la redacción oficial de OE2. |
| O5 · Calidad predictiva | Tabla por algoritmo y proyecto, macros y auditoría de criterios previos. [Métricas](../pi14_revision/D/criterios_y_metricas.md) | Aprobación previa de nuevos criterios de calidad. |
| O8 · Extracción | Demostración ejecutada con Lizard 1.25.0 sobre C. Se obtuvieron NLOC, complejidad ciclomática y tokens por función. [Viabilidad](metricas/LEEME.md) | Verificar la equivalencia de las 21 entradas con un par fuente–fila de referencia. |
| O9 · Organización | Evidencias organizadas por prueba. | Confirmar con el profesor el registro formal de CP10 como fuera de alcance. |

## Pendiente

| Observación | Trabajo pendiente |
|---|---|
| Entrega narrativa | Guion preparado. Grabación y entrega pendientes. [Guion](../../docs/cierre_tesis/GUION_VIDEO.md) |
| Aprobaciones académicas | OE2, criterios de calidad OE1–OE3 y decisiones de alcance. [Lista de aprobaciones](../../docs/cierre_tesis/APROBACIONES_PROFESOR.md) |

## No ejecutado

| Observación | Limitación |
|---|---|
| O7 / CP10 · Usabilidad | **NO EJECUTADO** por decisión de alcance de la investigación. No hay evidencia empírica de satisfacción, facilidad de uso ni efectos en el tiempo humano de QA. Los borradores existentes son antecedentes de planificación. |

## Control de entrega

La suite local y el control de espacios para esta publicación se registran en [verificacion.txt](verificacion.txt).
