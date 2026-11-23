# OE3 · Ejecución completa Nested LOPO PI15

Se ejecuta el procedimiento versionado de research/entrenamiento_defectos.py sin reducir candidatos: nueve recetas por tres algoritmos, 27 configuraciones. Por cada uno de cinco proyectos externos, cuatro validaciones internas seleccionan una receta por algoritmo. Una búsqueda global separada reserva sucesivamente cada uno de los cinco proyectos y ajusta un candidato final con toda la cohorte principal. La evaluación externa mide el procedimiento de selección; el candidato global no tiene evaluación independiente en un sexto proyecto.

## Entorno fijado

Python 3.13.0 en Windows, semilla 42 y PYTHONHASHSEED=42, un hilo mediante threadpoolctl. Los paquetes de investigación están fijados en requirements_fijados.txt; entorno_completo.txt conserva las versiones instaladas. entorno.json identifica las bibliotecas numéricas nativas, la huella del script, el hash de configuración y los artefactos que se protegen. Los archivos del experimento quedan en ejecucion_completa.

Para reanudar con el mismo entorno y los mismos cinco CSV verificados, desde la raíz del repositorio:

    python -B evidencias/pi15/oe3/ejecutar_completo.py

El script valida Python y las versiones y utiliza los checkpoints originales por candidato. Cada checkpoint queda ligado al hash de configuración y al orden de proyectos. Para una repetición íntegra nueva, copiar el lanzador y el fichero de requisitos a una carpeta nueva. No reutilizar los checkpoints entre entornos. Una modificación del estado o las versiones del entorno requiere una ejecución nueva identificada.

## Comparación y uso en la tesis

La salida comparacion_historico.csv conserva columnas nuevas e históricas para los 15 pares proyecto–algoritmo, las recetas seleccionadas y los deltas de F1, AUC-ROC y AP. sha256_salidas.json identifica los archivos obtenidos. Se requiere verificar que los seis checkpoints de búsqueda contienen los 27 candidatos completos y que no hubo errores antes de cerrar el ensayo.

Para OE3 se recomienda utilizar la nueva tabla completa y reproducible, identificada con este entorno y esta fecha, como resultado de la ejecución PI15, previa revisión del profesor. Las tablas históricas se deben conservar como antecedente y comparación de sensibilidad. La nueva ejecución no recupera por sí sola el entorno original de Colab ni demuestra reproducción exacta. Los resultados exploratorios de O1 mantienen su experimento y sus huellas. El modelo global candidato se guarda únicamente en la carpeta experimental y no reemplaza el E6 ni el calibrador del prototipo.

## Completitud verificada

Se verificaron los seis checkpoints con 27 candidatos completos sin errores, 675 ajustes candidatos, 15 evaluaciones externas por algoritmo, una selección global y las comparaciones adicionales del script. El candidato global es XGBoost/E5_SMOTE_MI y queda únicamente en ejecucion_completa/modelo_general_cpdp.joblib. E6 y su calibrador operativo conservan sus bytes. Se comprobó cada SHA-256 del manifiesto de salida. Un atributo Git local mantiene los bytes originales de las salidas, incluidos sus finales de línea, para conservar esas huellas al publicarlas.

[Validación](validacion_completitud.json) · [Resultados nuevos y contraste histórico](RESULTADOS_OE3.md)
