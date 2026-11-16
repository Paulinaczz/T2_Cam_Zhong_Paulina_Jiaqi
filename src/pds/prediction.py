"""M04/M06/M07: inferencia, interpretación y ranking de módulos."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .errors import ModelError
from .model import ModelArtifact
from .validation import ValidatedInput

SCORE_TYPE = "margen_svm_no_calibrado"

# Coeficientes sigmoides validados sobre los 11 690 márgenes OOF de los 5 proyectos históricos
DEFAULT_CALIBRATOR_COEF = 0.77433473
DEFAULT_CALIBRATOR_INTERCEPT = -1.28524283


def calibrate_probabilities(margins: np.ndarray, calibrator: object = None) -> np.ndarray:
    """Calcula la probabilidad P(defecto) in [0, 1] mediante la sigmoide logística ajustada (Platt scaling)."""
    m = np.asarray(margins, dtype=float)
    if calibrator is not None and hasattr(calibrator, "predict_proba"):
        return np.asarray(calibrator.predict_proba(m), dtype=float)
    # Regresión logística sigmoide estándar de respaldo
    return 1.0 / (1.0 + np.exp(-(DEFAULT_CALIBRATOR_COEF * m + DEFAULT_CALIBRATOR_INTERCEPT)))


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


def compare_strategies(valid: ValidatedInput, artifact: ModelArtifact) -> pd.DataFrame:
    """Compara las 3 estrategias: Operativa (Margen SVM), Experimental (Prob/LOC) y Referencia (ManualUp)."""
    expected = list(artifact.manifest["columnas"])
    if list(valid.features.columns) != expected:
        raise ModelError("El orden/esquema de características no coincide con el del pipeline")
    pipe = artifact.pipeline
    try:
        labels = np.asarray(pipe.predict(valid.features), dtype=int).ravel()
        margins = np.asarray(pipe.decision_function(valid.features), dtype=float).ravel()
    except Exception as ex:
        raise ModelError("Error al ejecutar el pipeline durante la comparación de estrategias") from ex

    calibrator = getattr(artifact, "calibrator", None)
    probs = calibrate_probabilities(margins, calibrator)

    if "loc" not in valid.features.columns:
        raise ModelError("La métrica 'loc' es obligatoria para la priorización por esfuerzo")
    raw_loc = np.asarray(valid.features["loc"], dtype=float).ravel()
    loc_cost = np.maximum(raw_loc, 1.0)
    density = probs / loc_cost

    n = len(valid.features)
    ids = np.arange(n)

    # 1. Prioridad Operativa (SVM Margin decreciente)
    order_svm = np.lexsort((ids, -margins))
    rank_svm = np.empty(n, dtype=int)
    rank_svm[order_svm] = np.arange(1, n + 1)

    # 2. Prioridad Experimental (Probabilidad / LOC decreciente)
    order_density = np.lexsort((ids, -density))
    rank_density = np.empty(n, dtype=int)
    rank_density[order_density] = np.arange(1, n + 1)

    # 3. Prioridad Referencia / Línea Base (ManualUp: LOC ascendente)
    order_manualup = np.lexsort((ids, loc_cost))
    rank_manualup = np.empty(n, dtype=int)
    rank_manualup[order_manualup] = np.arange(1, n + 1)

    comp = pd.DataFrame({
        "id_modulo": valid.identifiers.to_numpy(),
        "loc": raw_loc,
        "clase_predicha": labels,
        "score_riesgo_svm": margins,
        "prioridad_operativa_svm": rank_svm,
        "probabilidad_calibrada": probs,
        "densidad_riesgo_loc": density,
        "prioridad_experimental_calibrada_loc": rank_density,
        "prioridad_referencia_manualup": rank_manualup,
    })
    return comp.sort_values("prioridad_operativa_svm", ascending=True).reset_index(drop=True)


def csv_comparison_results(frame: pd.DataFrame) -> bytes:
    """Exportación CSV de la tabla comparativa con sanitización de identificadores."""
    safe = frame.copy()
    safe["id_modulo"] = safe["id_modulo"].astype(str).apply(
        lambda value: "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value
    )
    return safe.to_csv(index=False, float_format="%.6f").encode("utf-8-sig")
