# T10 y T11 · Comprobaciones documentales disponibles

## T10 · Datos

Se verificaron por separado los cinco CSV utilizados por el experimento. Para cada archivo coinciden la huella local, la del manifiesto histórico del proyecto y la descarga desde una versión fijada del espejo ApoorvaKrisna/NASA-promise-dataset-repository. Se guardan URL inmutable, commit del espejo, último commit del archivo y SHA-256. La copia JM1 tiene 13 204 filas. Este control permite identificar la copia usada y repetir el experimento.

La ficha de JM1 de Tera-PROMISE describe otra copia de 10 885 registros y advierte diferencias entre versiones. Las fichas de CM1 y PC1 mencionan versiones limpiadas distintas. Esas referencias contextualizan la familia de datos y no certifican identidad con los CSV congelados de esta tesis. La página actual de KC1 tiene metadatos sobre trazabilidad de requisitos que no permiten acreditar directamente el CSV de 2 109 filas usado aquí. Por tanto, la certificación documental de la cadena hasta NASA sigue parcial. Los datos usados se deben citar como copias del espejo identificado y separar de las versiones depuradas de otros autores.

- [Manifiesto por archivo y copia](datasets_verificados.csv)
- [Verificación y URLs fijadas](datasets_verificados.json)
- [Tera-PROMISE JM1](https://openscience.us/repo/defect/mccabehalsted/jm1.html)
- [Tera-PROMISE CM1](https://openscience.us/repo/defect/mccabehalsted/CM1.html)
- [Tera-PROMISE KC1](https://openscience.us/repo/defect/mccabehalsted/kc1.html)
- [Tera-PROMISE KC2](https://openscience.us/repo/defect/mccabehalsted/kc2.html)
- [Tera-PROMISE PC1](https://openscience.us/repo/defect/mccabehalsted/pc1.html)
- Shepperd, Song, Sun y Mair (2013). Data Quality: Some Comments on the NASA Software Defect Datasets. Se documentan diferencias entre versiones y la necesidad de explicitar procedencia y preprocesamiento. [Registro de los autores](https://bura.brunel.ac.uk/handle/2438/7926) · [DOI](https://doi.org/10.1109/TSE.2013.11)

## T11 · Figuras

Se leyó la revisión PI15 del 17/11/2026 y la tesis T2_Tesis_Cam_Zhong_Paulina_Jiaqi_15-11.docx aportadas por la tesista. Las imágenes que preceden a las leyendas de 6.1 y 6.2 son word/media/image7.png y word/media/image8.png. Difieren de los PNG del repositorio en bytes porque la tesis utiliza escala de grises. Al convertir ambas versiones a L con Pillow, las dimensiones y todos los píxeles coinciden exactamente.

La figura 6.1 corresponde a curvas_recall_LOC.png y la 6.2 a delta_por_proyecto_IC95.png. La cadena de generación es la siguiente:

| Archivo de imagen | Datos representados | Generador |
|---|---|---|
| research/experimentos/estrategia_esfuerzo/principal_deduplicada/curvas_recall_LOC.png | resumen_macro_por_metodo_y_presupuesto.csv de la misma carpeta | research/experimentos/estrategia_esfuerzo/cpdp_estrategia_esfuerzo.py, función ejecutar, savefig en línea 226 |
| research/experimentos/estrategia_esfuerzo/principal_deduplicada/delta_por_proyecto_IC95.png | diferencias_20pct_LOC_por_proyecto.csv de la misma carpeta | mismo script y función, savefig en línea 239 |

La celda 22 (índice desde cero) de research/Entrenamiento_Prediccion_Defectos.ipynb contiene la versión integrada del generador. Son figuras de la estrategia exploratoria de esfuerzo. No se reinterpretan como resultados de la nueva búsqueda Nested LOPO. [Huellas de imágenes, CSV y generador](figuras_candidatas.json)

Texto de fuente propuesto para 6.1: «Elaboración propia a partir de research/experimentos/estrategia_esfuerzo/principal_deduplicada/resumen_macro_por_metodo_y_presupuesto.csv. Generada por cpdp_estrategia_esfuerzo.py, función ejecutar, línea 226; versión integrada en la celda 22 del notebook. Representación en escala de grises».

Texto de fuente propuesto para 6.2: «Elaboración propia a partir de research/experimentos/estrategia_esfuerzo/principal_deduplicada/diferencias_20pct_LOC_por_proyecto.csv. Generada por cpdp_estrategia_esfuerzo.py, función ejecutar, línea 239; versión integrada en la celda 22 del notebook. Intervalos bootstrap condicionales y representación en escala de grises».

T11 quedó comprobada técnicamente. Falta sustituir las leyendas genéricas en el archivo final de tesis. Los DOCX fuente se mantuvieron intactos.
