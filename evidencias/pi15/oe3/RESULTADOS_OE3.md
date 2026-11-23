# Resultados oficiales propuestos de OE3 para PI15

La búsqueda completa repitió las 27 configuraciones en cada pliegue interno de los cinco proyectos externos. Estas métricas se calcularon con la receta seleccionada internamente para cada algoritmo. Cada proyecto tiene el mismo peso en el promedio macro.

| Algoritmo | F1 macro nuevo | F1 histórico | AUC-ROC nuevo | AP nueva |
|---|---:|---:|---:|---:|
| XGBoost | 0.423066 | 0.398280 | 0.711975 | 0.380567 |
| SVM | 0.413096 | 0.412223 | 0.727687 | 0.348831 |
| Random Forest | 0.361601 | 0.360630 | 0.693271 | 0.360133 |

Se recomienda utilizar la tabla nueva para OE3 en la tesis final, de acuerdo con la sección 5.1 de PI15, identificándola con el entorno de la versión v1.0-tesis. El orden por F1 cambia a XGBoost, SVM y Random Forest. El mayor AUC macro corresponde a SVM y la mayor AP a XGBoost. Las tablas anteriores permanecen como resultados históricos de Colab.

Este procedimiento selecciona una receta diferente por pliegue y algoritmo. El E6 de la aplicación es una receta fija ajustada globalmente. Su evaluación fija tiene otro estimando y no se debe mezclar con el promedio externo de selección. La validación Nested LOPO del procedimiento tampoco aporta un sexto proyecto independiente para el archivo global.

Las decisiones y resultados de la comparación exploratoria de E6 frente a ManualUp pertenecen a otro experimento. Se conservaron sus datos y conclusiones. Los cambios de orden entre clasificadores no cambian esa conclusión experimental de OE4.

[Resultados por proyecto y algoritmo](ejecucion_completa/comparacion_algoritmos_outer.csv) · [Macros nuevos](ejecucion_completa/resumen_algoritmos_externos.csv) · [Comparación macro con histórico](comparacion_macro.csv) · [Entorno y procedimiento](LEEME.md)
