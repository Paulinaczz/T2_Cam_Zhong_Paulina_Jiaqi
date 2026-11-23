# Corrección de UI04

El texto de Comparación de Estrategias mostraba CM1 y PC1 como favorables al ranking de probabilidad calibrada/LOC. El CSV de diferencias en Recall@20 % LOC identifica CM1 (+4,347826 p.p.) y JM1 (+0,851703 p.p.). PC1 tiene delta negativo (−1,428571 p.p.). La revisión confirmó que la metodología ya enumeraba CM1 y JM1. Las menciones a CM1 y PC1 en capturas o informes históricos registran lo observado en esa versión.

La interfaz ahora muestra CM1 y JM1. La prueba ejecuta UI04 en AppTest con una base aislada, deriva del CSV el conjunto de proyectos con delta positivo y comprueba los nombres y recuentos del texto renderizado. Las cifras y los artefactos de O1 se conservaron.

[CSV experimental](../../../research/experimentos/estrategia_esfuerzo/principal_deduplicada/diferencias_20pct_LOC_por_proyecto.csv) · [Prueba de regresión](../../../tests/test_ui04_experimental_summary.py) · [Verificación de la suite](../F/verificacion_final.txt)
