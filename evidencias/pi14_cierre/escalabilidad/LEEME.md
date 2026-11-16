# Ensayo del límite de 20 000 módulos

El lote sintético replica cíclicamente 18 perfiles de la muestra del repositorio y asigna identificadores únicos a 20 000 filas con 21 métricas. El CSV ocupa 2 226 768 bytes (2,12 MiB), por debajo de 10 MiB. E6 y el calibrador se leen desde los artefactos verificados de la rama.

Se mide de manera secuencial, en un solo proceso, con el lote ya cargado en memoria y el modelo ya abierto. Cada repetición ejecuta la lectura y validación de los bytes, el servicio real de comparación con inferencia E6, calibración y cálculo de los tres rankings, y la exportación comparativa a bytes CSV. El total se cronometra por repetición. El cálculo del p95 utiliza interpolación lineal. El alcance excluye arranque, esperas de servidor, persistencia, inferencia adicional del ranking operativo, transferencia y renderizado de Streamlit.

Equipo Windows 10, AMD Ryzen 5 3600, seis núcleos físicos, 12 procesadores lógicos y 17 102 508 032 bytes de RAM física notificada. Se registró Python 3.13 y los backends nativos cargados. No se fijó afinidad ni se midieron pico de memoria o usuarios concurrentes. Hubo actividad local de diagnóstico de CP09 durante parte de las corridas. La concentración en 18 perfiles y una sola máquina limita la extrapolación a lotes heterogéneos, otros equipos o despliegue en producción. La meta original de 5 s aplica al lote de 18 módulos.

Desde la raíz del repositorio:

    python evidencias/pi14_cierre/escalabilidad/medir_limite.py --salida results_tmp/escalabilidad_20000

[Script del ensayo](medir_limite.py) · [Entrada sintética](ensayo_20000/entrada_sintetica.csv) · [Entorno](ensayo_20000/entorno.json) · [Mediciones individuales](ensayo_20000/mediciones.csv) · [Log](ejecucion.txt)

## Resultados de 30 corridas completas

| Fase | Mediana (s) | p95 (s) | Desviación muestral (s) |
|---|---:|---:|---:|
| Lectura y validación | 0,536120 | 0,623275 | 0,031218 |
| Comparación | 64,104672 | 67,042516 | 1,030854 |
| Exportación | 0,182497 | 0,194851 | 0,005468 |
| Total del flujo comparativo | 64,824879 | 67,837039 | 1,044501 |

El tiempo cronometrado acumulado fue de 32.61 minutos. El tiempo de comparación concentra la mayor parte del total. El p95 total se calculó sobre los totales individuales, sin sumar los percentiles de cada fase. [Resumen JSON](ensayo_20000/resumen.json)
