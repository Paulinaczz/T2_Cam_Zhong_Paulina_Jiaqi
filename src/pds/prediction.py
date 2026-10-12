"""M04/M06/M07: inferencia, interpretación y ranking de módulos."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .errors import ModelError
from .model import ModelArtifact
from .validation import ValidatedInput

SCORE_TYPE = "margen_svm_no_calibrado"


def predict(valid: ValidatedInput, artifact: ModelArtifact) -> pd.DataFrame:
    expected = list(artifact.manifest["columnas"])
    if list(valid.features.columns) != expected:
        raise ModelError("El orden/esquema de características no coincide con el del pipeline")
    pipe = artifact.pipeline
    try:
        labels = np.asarray(pipe.predict(valid.features), dtype=int).ravel()
        margins = np.asarray(pipe.decision_function(valid.features), dtype=float).ravel()
    except Exception as ex:
        raise ModelError("Error al ejecutar el pipeline. Verifica el entorno y el esquema") from ex
    if len(labels) != len(valid.features) or len(margins) != len(valid.features):
        raise ModelError("La longitud de predicciones no coincide con los registros")
    if not set(labels).issubset({0, 1}) or not np.isfinite(margins).all():
        raise ModelError("El modelo devolvió clases o scores incompatibles")
    # El clasificador SVC tiene clases [0,1], por lo que el signo positivo es clase 1.
    try:
        classes = pipe.named_steps["model"].classes_.tolist()
    except (AttributeError, KeyError) as ex:
        raise ModelError("No se puede verificar el orden de las clases") from ex
    if classes != [0, 1]:
        raise ModelError("El modelo no utiliza las clases esperadas [0, 1]")
    df = pd.DataFrame({
        "id_modulo": valid.identifiers.to_numpy(),
        "clase_predicha": labels,
        "score_riesgo": margins,
        "tipo_score": SCORE_TYPE,
    })
    df["interpretacion"] = np.where(df["clase_predicha"] == 1, "Potencialmente defectuoso", "No defectuoso previsto")
    df = df.sort_values("score_riesgo", ascending=False, kind="stable").reset_index(drop=True)
    df.insert(0, "prioridad", np.arange(1, len(df) + 1))
    return df


def csv_results(frame: pd.DataFrame) -> bytes:
    """Exportación CSV con defensa frente a fórmulas Excel en identificadores."""
    safe = frame.copy()
    # Excel puede evaluar fórmulas en una columna de identificador textual.
    safe["id_modulo"] = safe["id_modulo"].astype(str).apply(
        lambda value: "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value
    )
    return safe.to_csv(index=False, float_format="%.8f").encode("utf-8-sig")
