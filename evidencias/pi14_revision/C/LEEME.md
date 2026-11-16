# Casos ejecutados en Streamlit

| Caso | Resultado observado | Evidencia |
|---|---|---|
| CP02 | Rechazado por falta de LOC | [Captura](CP02_sin_loc.jpg) |
| CP03 | Rechazados un infinito y un texto en campos numéricos | [Infinito](CP03_inf.jpg) · [Texto](CP03_texto.jpg) |
| CP04 | El CSV se procesó y la exportación operativa escapó el identificador de prueba con apóstrofo | [Captura](CP04_exportacion.jpg) · [CSV descargado](CP04_exportacion.csv) |
| CP11 | Rechazados identificadores duplicados y archivo XLSX. Streamlit rechazó XLSX en el selector antes de validar el CSV | [Duplicado](CP11_id_duplicado.jpg) · [Extensión](CP11_extension.jpg) |
| CP12 | Inicio bloqueado por SHA-256 de E6 en una copia aislada alterada | [Captura](CP12_hash.jpg) |

La base de la prueba solo contiene la ejecución válida de CP04 y 18 predicciones. CP12 se ejecutó con servidor y copia separados. La comprobación al terminar verificó los artefactos originales contra sus manifiestos. Las capturas corresponden al navegador y la base de prueba y la copia alterada quedan fuera del paquete. Los mensajes observados se conservan junto a las capturas. [Huellas y comprobaciones](verificacion.json)
