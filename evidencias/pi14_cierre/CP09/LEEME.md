# CP09 · Localización de las diferencias por etapa

**Dictamen: parcialmente comprobado.** La repetibilidad local a semilla fija está demostrada. El cambio aislado del paquete NumPy reproduce una receta histórica adicional, pero el primer punto de divergencia entre Colab y Windows no se puede determinar para todo CP09 con los archivos disponibles.

## Referencia histórica y trazas locales

Se mantuvieron los cinco archivos NASA/PROMISE con el SHA-256 del plan, la cohorte deduplicada de 11 690 filas y el orden de los pliegues. La huella de configuración coincide con la archivada. Para PC1 Random Forest E2_ADASYN y KC1 SVM E6_ADASYN_MI, se registraron sucesivamente hashes de archivos, matrices y etiquetas deduplicadas por proyecto en orden, X/y de train y test en orden, imputación, escalado, conjunto y orden de columnas, dos consultas de vecinos de ADASYN, muestras sintéticas, score continuo y predicciones. En Random Forest el score es la probabilidad de clase positiva; en SVM es el margen. Las trazas no incluyen vectores completos del corpus ni guardan modelos reentrenados.

El notebook original disponible y el ZIP de referencias preservan resultados agregados y la selección histórica, pero no preservan los tensores intermedios históricos, la matriz de vecinos, los resultados de balanceo, ni las predicciones por fila de las recetas de CP09 contrastadas. El CSV de predicciones de estrategia por esfuerzo corresponde a otro experimento y no se usó como identificación de esos artefactos. La versión completa de Python, SciPy, NumPy y las bibliotecas nativas del Colab histórico tampoco se pueden fijar a partir de esos archivos. Por ello los primeros cambios de la tabla son entre trazas locales controladas.

## Cambios controlados

Todos los contrastes conservaron los datos, código de receta, semilla 42 y configuración base, salvo el factor señalado. Una etapa distinta se identifica por el hash de sus salidas. Para vecinos se guardan por separado el orden devuelto y el conjunto por fila.

| Variable aislada | Primer cambio local y efecto |
|---|---|
| Desactivar la reducción de distancias Cython | En PC1, el primer hash distinto es el de vecinos globales. Cambió también la pertenencia a los conjuntos globales y minoritarios. Las muestras sintéticas pasaron de 5 666 a 5 668 y el F1 de 0,334975 a 0,311558. KC1 usa kd-tree con esta receta y no cambió. |
| Reordenar empates exactos por índice dentro de los k vecinos devueltos | Cambió el orden de vecinos desde la consulta global en ambos proyectos, con la misma pertenencia. No se resuelven empates en la frontera de k. Como ADASYN omite la primera posición y elige posiciones entre los vecinos de la clase minoritaria, el orden puede cambiar el balanceo. PC1 conservó 5 666 muestras y cambió su F1 a 0,341709. KC1 pasó de 6 027 a 6 069 muestras y de 0,416667 a 0,419106 en F1. |
| Hilos nativos 1 → 2 | Hashes de las etapas y métricas idénticos en ambos controles. Es evidencia para este rango y equipo. |
| NumPy 2.5.5 → 2.1.3 | El primer cambio fue el escalado en ambos proyectos. En PC1 cambió también la membresía de vecinos y hubo 5 669 muestras sintéticas. F1 0,291457, AUC 0,781683 y AP 0,263334 coinciden con los históricos dentro de 10⁻¹². En KC1 se seleccionaron las mismas diez columnas, los vecinos y las clases predichas coincidieron y el margen cambió a nivel de bytes, conservando las métricas. La rueda de NumPy también carga otra versión de OpenBLAS. El ensayo aísla el paquete y no separa ambos componentes. |
| SciPy 1.18.1 → 1.16.3 | No cambió ninguna etapa ni métrica de los dos controles. |

Con NumPy 2.1.3 se ampliaron las comparaciones a las 15 recetas externas archivadas. **4 de 15** reproducen las tres métricas históricas a tolerancia absoluta 10⁻¹², frente a **3 de 15** con la versión base. La mejora es PC1–Random Forest; las tres recetas de JM1 ya coincidían. Los máximos residuos de la variante siguen siendo 0,041667 en F1, 0,025390 en AUC y 0,015808 en AP. Esta coincidencia parcial y el cambio en la primera etapa de PC1 demuestran una explicación reproducible en la máquina local. No identifican la versión exacta que utilizó Colab.

## Reproducción

Desde la raíz del repositorio con el entorno de investigación documentado y los CSV originales ya verificados:

    python evidencias/pi14_cierre/CP09/trazar_etapas.py --datos research/raw/pi14 --salida results_tmp/traza_base.json --variante base

Repetir en archivos distintos con backend, empates y hilos2. Para numpy y scipy, instalar solo el paquete de contraste en un directorio separado con pip install --no-deps --target, y usar PYTHONPATH para anteponer ese directorio al entorno base. El lanzador valida la versión cargada. Las trazas de esta entrega están en trazas y el lanzador resumir_trazas.py las compara. Para NumPy, contrastar_numpy.py repite las 15 recetas y guarda las métricas de ambas versiones y el histórico.

[Comparación de etapas](comparacion_etapas.csv) · [CSV de las 15 recetas](numpy_15_recetas.csv) · [Trazas](trazas/) · [Lanzador](trazar_etapas.py)

## Condición de cierre

Se necesitan el entorno histórico congelado o un Colab de referencia con versiones y backend nativo documentados, y trazas equivalentes para comparar por etapa hasta las predicciones. A continuación corresponde repetir la búsqueda Nested LOPO de 27 configuraciones con esa referencia. Repetir la búsqueda con una pila elegida retrospectivamente mediría otro entorno y no demostraría reproducción histórica. La búsqueda completa no se ejecutó. Se preservaron todos los CSV y artefactos históricos.
