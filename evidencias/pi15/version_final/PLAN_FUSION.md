# Preparación de la versión v1.0-tesis

Comprobación inicial de GitHub realizada el 22 de noviembre de 2026. El PR #3 está abierto y sin fusionar. La base main es 473669c87e810f967219112804833bbde533bede y su cabeza es 9dfc66e2bc3bfc52b4ffec357837a99f8714d562. GitHub informó mergeable=true y mergeable_state=clean. La comprobación local merge-tree produjo un árbol sin conflictos. Se aprobaron 16 pruebas del checkout local de la rama. Ambos artefactos coinciden con los SHA-256 de sus manifiestos.

## Alcance de la fusión propuesta

- main incorporaría el calibrador serializado y su verificación, la comparación de margen SVM, densidad calibrada/LOC y ManualUp, y la corrección de rótulo CM1/JM1.
- Se incorporan las pruebas y evidencias publicadas de CP01, CP05, casos negativos, mediciones al límite de 20 000 módulos, CP09 parcial y la demostración parcial con Lizard.
- El pipeline E6 conserva sus bytes. Los cambios de código incorporan la carga del calibrador y los servicios de comparación.
- Se propone añadir el cierre documental local de CP10 NO EJECUTADO y docs/cierre_tesis, con el informe para tesis, el guion y las aprobaciones pendientes. Son cinco archivos versionados modificados y tres documentos nuevos.
- La nueva búsqueda Nested LOPO vive en evidencias/pi15/oe3. Su modelo reentrenado es un candidato experimental. No sustituye artefactos operativos.

## Condición de ejecución

El usuario autorizó publicar el cierre documental, fusionar mediante merge commit, validar main y crear la etiqueta y release v1.0-tesis. El cierre documental se publicó en 88ea08b. Las comprobaciones posteriores deben apuntar al commit definitivo de main y verificar ambas huellas. Se incluirán en los adjuntos del release para evitar modificar el commit después de etiquetarlo.

[Hashes y comprobación previa](preparacion.json)
