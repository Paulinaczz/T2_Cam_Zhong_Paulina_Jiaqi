# CP09 · Protocolo y alcance

Fuente original: PI11–PI12, ES09/CP09, sección 2.3. El criterio documentado pide ejecutar el pipeline con cinco CSV NASA/PROMISE y conservar CSV y JSON comparables, con tres algoritmos y 27 configuraciones verificables. No fija un número concreto de repeticiones ni tolerancia numérica. El examen local es una propuesta técnica, con 42 repetida dos veces y 43 como sensibilidad; este diseño no redefine la aceptación académica.

## Dos alcances

- Repetición de recetas históricas. Reentrena secuencialmente las recetas que figuran por algoritmo y proyecto externo en el CSV Nested LOPO archivado. Conserva los cinco pliegues, los tres algoritmos y las 21 métricas. Omite la selección interna para medir el efecto de repetir entrenamiento en un tiempo razonable.
- CP09 completo. El parámetro --nested-completo llama a la búsqueda original con 27 configuraciones para cada pliegue y a la selección global. Solo escribe en el directorio nuevo de salida. La búsqueda requiere 5×(27×4) + 27×5 = 675 ajustes candidatos por repetición, además de pruebas externas y ajustes finales. Tres repeticiones superan 2 000 ajustes candidatos, por lo que queda pendiente reservar tiempo de cómputo para la serie completa.

## Controles e interpretación

Usar los cinco CSV originales indicados en research/auditoria/fuentes_y_sha256.csv. El lanzador bloquea el ensayo si no coinciden los cinco hashes, la huella de la cohorte principal o las tres dependencias fijadas en la configuración histórica. Deduplicar una sola vez con semilla 42 y conservar los pliegues para separar cambios de entrenamiento de cambios de corpus. Registrar versiones, un hilo y semilla por ejecución.

En el mismo entorno y con semilla 42 fija, se espera igualdad de los datos, pliegues, configuraciones seleccionadas en el modo completo y CSV canónico de métricas. Una divergencia se documenta, incluyendo variación flotante. El binario entrenado puede incorporar metadatos dependientes de la ejecución; sus hashes y los tiempos no se exigen idénticos. Con semilla 43, mantienen igualdad los bytes de entrada, la huella de la cohorte, los pliegues y el esquema. Pueden variar sobremuestreo, selección de características, estimadores estocásticos y métricas. Se reportan F1 de la clase positiva, AUC-ROC y Average Precision por proyecto y algoritmo, junto con diferencias pareadas y SHA-256. Dos semillas distintas ilustran sensibilidad y no estiman su distribución con precisión.

Desde la raíz del repositorio, con los CSV verificados en research/raw/pi14 y dependencias instaladas, ejecutar:

    python -B evidencias/pi14_revision/A/repetir_cp09.py --datos research/raw/pi14 --salida results_tmp/cp09_recetas

Para la búsqueda completa añadir --nested-completo y usar un directorio de salida nuevo. Ejecutar una sola instancia, guardar la salida de consola y proteger los artefactos operativos.

## Resultados ejecutados

Tres series secuenciales, 15 entrenamientos externos por serie y 45 en total. Las dos series con semilla 42 produjeron el mismo CSV byte a byte y el mismo SHA-256. El cambio a 43 alteró las 15 filas en cada métrica (diferencias absolutas > 10⁻¹²). Magnitudes máximas: F1 0,113008; AUC-ROC 0,020345; AP 0,036925.

Frente al CSV histórico Nested LOPO, la primera serie local con semilla 42 tiene divergencias en F1 (10 de 15; máximo 0,043518), AUC-ROC (12 de 15; máximo 0,025390) y AP (12 de 15; máximo 0,015808). Aunque coinciden fuentes, huella de cohorte y dependencias declaradas en la configuración histórica, el archivo histórico no identifica toda la pila numérica ni el hardware. La causa exacta sigue abierta. Las cifras históricas y la serie local se conservan como evidencias diferentes.

[Entorno](repeticion_recetas_fijas/entorno.json) · [Versiones para instalar](requirements_cp09.txt) · [Log](ejecucion.txt) · [Serie 42a](repeticion_recetas_fijas/semilla42_a/metricas.csv) · [Serie 42b](repeticion_recetas_fijas/semilla42_b/metricas.csv) · [Serie 43](repeticion_recetas_fijas/semilla43/metricas.csv) · [SHA-256 de salidas](repeticion_recetas_fijas/sha256.json) · [Deltas locales](repeticion_recetas_fijas/diferencias.csv) · [Contraste histórico](contraste_csv_historico.csv)

[Diagnóstico de la discrepancia histórica](diagnostico_discrepancia.md).
