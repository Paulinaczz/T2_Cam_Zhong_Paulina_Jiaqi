# CP10 · I-05 y validación de contenido

**Estado: borrador para 2–3 jueces, sin aplicar.** Fuentes: PI11–PI12 §1.3, §1.4, §2.3 CP10 y revisión O7. El texto del plan remite a anexos I-05/I-06, pero la copia disponible termina en I-03. Esta propuesta reconstruye los instrumentos a partir del diseño de CP10. Contrastar con los anexos originales si se recuperan.

## Ficha de juez

Código de juez: ______ | Especialidad y experiencia: ______ | Versión de instrumento: ______ | Fecha: ______

Revisar por separado relevancia, claridad y coherencia de cada tarea e ítem. Escala: 1 deficiente, 2 requiere revisión sustancial, 3 adecuado con cambios menores, 4 adecuado. Indicar cambios concretos en la matriz. Además, juzgar la suficiencia del conjunto, la equivalencia de entregables entre modalidades, la carga de trabajo y el encuadre ético.

Suficiencia global / elementos faltantes: __________________________________________________

Equivalencia de modalidades / sesgos: __________________________________________________

Dictamen (aplicar / revisar y volver a evaluar / rediseñar): _____________________________

## Matriz V de Aiken

Usar una fila por ítem y dimensión en la [matriz](matriz_aiken.csv). Fijar el número de jueces antes de evaluar. Para una escala 1–4, V = suma(r − 1)/(n × 3), solo con todas las puntuaciones válidas. Con dos jueces dejar J3 vacío. En una hoja configurada en español, en G2 y con F como tercera calificación, usar si son tres: =SI(CONTAR(D2:F2)=3;(SUMA(D2:F2)-3)/9;""). Para dos: =SI(CONTAR(D2:E2)=2;(SUMA(D2:E2)-2)/6;""). Aplicar validación de datos de enteros 1–4. El panel debe acordar la regla de revisión antes de puntuar. Con 2–3 jueces reportar V, número de jueces y comentarios por dimensión, y tratar la precisión como limitada.

## Guion moderado de tareas equivalentes

Reclutar al menos cinco adultos voluntarios con experiencia real en QA o desarrollo. Antes de empezar, obtener I-06 aprobado y consentido. Usar dos lotes equivalentes de práctica/evaluación, con 18 módulos sintéticos, los mismos campos y entregables; verificar sus claves y dificultad antes de la sesión. Para la hoja entregar el CSV métricas más las predicciones y márgenes E6 precalculados del lote, de modo que ambas modalidades permitan revisar idénticos resultados. La comparación del piloto cubre el flujo de trabajo de QA con datos precomputados. Documentar versiones de app y hoja, equipo, lote, duración y orden. Alternar el orden de modalidades y lotes. No mostrar la clave al participante. Leer las mismas instrucciones, permitir preguntas neutrales y registrar la asistencia que revele un paso o respuesta como ayuda crítica.

| Tarea | PDS-QA | CSV + hoja | Criterio observable |
|---|---|---|---|
| T1 Preparar entrada | Cargar el lote y consultar validación | Importar lote, revisar encabezados y contar filas | Identifica 18 módulos y verifica 21 métricas |
| T2 Interpretar el riesgo | Abrir resultado y leer clase y margen | Usar tabla precalculada de E6 y sus campos | Reporta clase y margen del módulo indicado y explica que el margen no es porcentaje |
| T3 Priorizar | Consultar ranking operativo | Ordenar margen descendente, desempatar por orden de entrada | Identifica los mismos tres módulos, en el orden esperado |
| T4 Exportar | Guardar ranking operativo | Exportar selección ordenada como CSV | CSV legible con identificadores, clases y margen esperados |
| T5 Recuperar evidencia | Usar historial e identificar la ejecución | Abrir registro de selecciones preparado para la sesión y recuperar el CSV | Identifica registro, lote y tres módulos del mismo ranking |

Por tarea, iniciar el cronómetro al terminar la instrucción y detenerlo al entregar respuesta, abandonar o alcanzar el límite común previamente fijado. Éxito = cumple la clave sin ayuda crítica. Registrar intentos, errores, ayudas, tiempo y observaciones en [observaciones.csv](observaciones.csv). Registrar motivos de abandono por separado. Meta piloto propuesta por PI11–PI12 para cinco participantes: al menos 4 de 5 completan al menos 4 de 5 tareas sin ayuda crítica. Si se supera n=5, conservar el recuento y acordar antes la regla para esa muestra.

### Encuesta por modalidad

Escala 1 totalmente en desacuerdo a 5 totalmente de acuerdo. Marcar no aplica si corresponde y documentar el motivo.

- U1. Me resultó fácil preparar el archivo para el análisis.
- U2. Entendí cómo se identificó el orden de revisión.
- U3. Pude guardar el ranking que necesitaba.
- U4. Pude recuperar la evidencia de mi análisis.
- U5. Usaría este procedimiento para priorizar módulos en QA.
- P1. ¿Qué paso causó más dificultad y por qué?

Registrar en [respuestas.csv](respuestas.csv). Reportar resultados descriptivos, con recuentos y denominadores por modalidad. La muestra piloto no sustenta generalización.
