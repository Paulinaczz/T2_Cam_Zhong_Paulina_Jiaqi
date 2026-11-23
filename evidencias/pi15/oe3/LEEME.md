# OE3 · Ejecución completa Nested LOPO PI15

Se ejecuta el procedimiento versionado de research/entrenamiento_defectos.py sin reducir candidatos: nueve recetas por tres algoritmos, 27 configuraciones. Por cada uno de cinco proyectos externos, cuatro validaciones internas seleccionan una receta por algoritmo. Una búsqueda global separada reserva sucesivamente cada uno de los cinco proyectos y ajusta un candidato final con toda la cohorte principal. La evaluación externa mide el procedimiento de selección; el candidato global no tiene evaluación independiente en un sexto proyecto.

## Entorno fijado

Python 3.13.0 en Windows, semilla 42 y PYTHONHASHSEED=42, un hilo mediante threadpoolctl. Los paquetes de investigación están fijados en requirements_fijados.txt; entorno_completo.txt conserva las versiones instaladas. entorno.json identifica las bibliotecas numéricas nativas, la huella del script, el hash de configuración y los artefactos que se protegen. Los archivos del experimento quedan en ejecucion_completa.

## Nueva ejecución y reanudación explícita

Desde la raíz del repositorio, con Python 3.13.0 y los paquetes de requirements_fijados.txt:

    python -m pip install -r evidencias/pi15/oe3/requirements_fijados.txt
    python -B evidencias/pi15/oe3/ejecutar_completo.py --salida results_tmp/oe3_nuevo

La carpeta de salida debe ser nueva, incluso si una carpeta existente está vacía. El directorio recibe entorno.json, comparacion_historico.csv, sha256_salidas.json y la subcarpeta ejecucion_completa. Las evidencias publicadas de OE3 y artifacts/models están protegidos como destinos. El script conserva las rutas de recursos de esta versión y permite especificar otra ubicación de datos con --datos.

Para reanudar una ejecución de trabajo compatible:

    python -B evidencias/pi15/oe3/ejecutar_completo.py --salida results_tmp/oe3_nuevo --reanudar

La reanudación exige entorno.json y ejecucion_completa. Antes de reutilizar los checkpoints comprueba Python, plataforma, versiones, bibliotecas nativas, código experimental, hashes de los artefactos y configuración de datos. Conserva la fecha inicial del entorno. Una incompatibilidad detiene el proceso. Los checkpoints de la búsqueda también comprueban la configuración y los proyectos.

### Restaurar los cinco CSV del release

Descargar PDS-QA_v1.0-tesis_evidencias.zip desde el [release estable](https://github.com/Paulinaczz/T2_Cam_Zhong_Paulina_Jiaqi/releases/tag/v1.0-tesis). Desde la raíz del checkout, pasar su ruta real al siguiente bloque. Se extraen exclusivamente las cinco entradas públicas verificadas y se comprueban sus SHA-256. Si ya existe un archivo diferente, el bloque se detiene antes de escribir.

    import hashlib
    import json
    import zipfile
    from pathlib import Path

    manifest = json.loads(Path("evidencias/pi15/trazabilidad/datasets_verificados.json").read_text())
    with zipfile.ZipFile("PDS-QA_v1.0-tesis_evidencias.zip") as archive:
        pending = []
        for row in manifest["archivos"]:
            path = Path("research/raw/pi14") / row["archivo"]
            payload = archive.read(path.as_posix())
            assert hashlib.sha256(payload).hexdigest() == row["sha256_local"]
            if path.exists():
                assert path.read_bytes() == payload, path
            else:
                pending.append((path, payload))
        for path, payload in pending:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(payload)

El ZIP y el checkout de Git tienen alcances distintos: las cinco entradas no están versionadas en Git. La restauración es necesaria en un checkout nuevo. Una nueva ejecución requiere tiempo de cómputo; los tests del lanzador verifican protección de salidas con datos temporales.

## Comparación y uso en la tesis

La salida comparacion_historico.csv conserva columnas nuevas e históricas para los 15 pares proyecto–algoritmo, las recetas seleccionadas y los deltas de F1, AUC-ROC y AP. sha256_salidas.json identifica los archivos obtenidos. Se requiere verificar que los seis checkpoints de búsqueda contienen los 27 candidatos completos y que no hubo errores antes de cerrar el ensayo.

Para OE3 se recomienda utilizar la nueva tabla completa y reproducible, identificada con este entorno y esta fecha, como resultado de la ejecución PI15, previa revisión del profesor. Las tablas históricas se deben conservar como antecedente y comparación de sensibilidad. La nueva ejecución no recupera por sí sola el entorno original de Colab ni demuestra reproducción exacta. Los resultados exploratorios de O1 mantienen su experimento y sus huellas. El modelo global candidato se guarda únicamente en la carpeta experimental y no reemplaza el E6 ni el calibrador del prototipo.

## Completitud verificada

Se verificaron los seis checkpoints con 27 candidatos completos sin errores, 675 ajustes candidatos, 15 evaluaciones externas por algoritmo, una selección global y las comparaciones adicionales del script. El candidato global es XGBoost/E5_SMOTE_MI y queda únicamente en ejecucion_completa/modelo_general_cpdp.joblib. E6 y su calibrador operativo conservan sus bytes. Se comprobó cada SHA-256 del manifiesto de salida. Un atributo Git local mantiene los bytes originales de las salidas, incluidos sus finales de línea, para conservar esas huellas al publicarlas.

[Validación](validacion_completitud.json) · [Resultados nuevos y contraste histórico](RESULTADOS_OE3.md)
