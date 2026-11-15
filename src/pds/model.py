"""M05: verificación de integridad y carga de un modelo de origen confiable.

No se admiten modelos subidos por el usuario: Joblib/Pickle puede ejecutar código
al deserializar. El SHA-256 detecta cambios accidentales, no autentica al autor.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import joblib
import numpy as np
from importlib.metadata import version, PackageNotFoundError

# Guardado en Colab v11: scikit-learn 1.6.1 / imbalanced-learn 0.14.2.
REQUIRED_VERSIONS = {"scikit-learn":"1.6.1", "imbalanced-learn":"0.14.2"}


def ensure_compatible_versions():
    for package, needed in REQUIRED_VERSIONS.items():
        try:
            installed=version(package)
        except PackageNotFoundError as ex:
            raise ModelError(f"Falta {package}=={needed}. Instala requirements.txt") from ex
        if installed != needed:
            raise ModelError(
                f"Version incompatible de {package}: instalada {installed}, requerida {needed}. "
                "El modelo entrenado se serializo con esas versiones; instala requirements.txt."
            )


from .errors import ModelError


@dataclass(frozen=True)
class CalibratorArtifact:
    estimator: object
    coef: float
    intercept: float
    manifest: dict
    sha256: str
    path: Path

    def predict_proba(self, margins: np.ndarray) -> np.ndarray:
        m = np.asarray(margins, dtype=float)
        return 1.0 / (1.0 + np.exp(-(self.coef * m + self.intercept)))


@dataclass(frozen=True)
class ModelArtifact:
    pipeline: object
    manifest: dict
    sha256: str
    path: Path
    calibrator: CalibratorArtifact | None = None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_model(directory: Path) -> ModelArtifact:
    directory = Path(directory)
    model_path = directory / "modelo_predictivo_pds.joblib"
    integrity_path = directory / "integridad_modelo.json"
    manifest_path = directory / "metadatos_modelo.json"
    for f in (model_path, integrity_path, manifest_path):
        if not f.is_file():
            raise ModelError(f"No se encuentra el archivo del modelo: {f.name}")
    try:
        integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
        manifest_file = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        raise ModelError("No se pudieron leer los metadatos del modelo") from ex
    actual_sha = file_sha256(model_path)
    if integrity.get("sha256") != actual_sha:
        raise ModelError("El SHA-256 del pipeline no coincide con el valor registrado")
    ensure_compatible_versions()
    try:
        bundle = joblib.load(model_path)
    except Exception as ex:
        raise ModelError("No se pudo abrir el pipeline. Comprueba las versiones de las librerías") from ex
    if not isinstance(bundle, dict) or not all(k in bundle for k in ("pipeline", "columnas", "manifest")):
        raise ModelError("El artefacto no tiene la estructura esperada")
    pipeline = bundle["pipeline"]
    cols = bundle["columnas"]
    if not isinstance(cols, (list, tuple)) or len(cols) != 21 or len(cols) != len(set(cols)):
        raise ModelError("El artefacto no contiene exactamente 21 métricas únicas")
    if list(cols) != manifest_file.get("columnas") or bundle["manifest"] != manifest_file:
        raise ModelError("El manifiesto externo no coincide con los metadatos del modelo")
    if manifest_file.get("algoritmo") != "SVM" or manifest_file.get("escenario") != "E6_ADASYN_MI":
        raise ModelError("No se reconoce la configuración del modelo esperado")
    if not hasattr(pipeline, "predict") or not hasattr(pipeline, "decision_function"):
        raise ModelError("El modelo no implementa los métodos de predicción necesarios")
    # Verificación de las capas para no reutilizar solo el clasificador.
    steps = getattr(pipeline, "named_steps", {})
    if not all(k in steps for k in ("imputer", "scaler", "selection", "sampler", "model")):
        raise ModelError("Faltan transformaciones del pipeline original")
    if steps["selection"].__class__.__name__ != "SelectKBest" or steps["sampler"].__class__.__name__ != "ADASYN" or steps["model"].__class__.__name__ != "SVC":
        raise ModelError("Los estimadores del pipeline no corresponden al escenario E6_ADASYN_MI")
    calibrator = load_calibrator(directory)
    return ModelArtifact(pipeline=pipeline, manifest=manifest_file, sha256=actual_sha, path=model_path, calibrator=calibrator)


def load_calibrator(directory: Path) -> CalibratorArtifact | None:
    directory = Path(directory)
    calib_path = directory / "calibrador_probabilidad_e6.joblib"
    integrity_path = directory / "integridad_calibrador.json"
    manifest_path = directory / "metadatos_calibrador.json"
    if not calib_path.is_file() or not integrity_path.is_file() or not manifest_path.is_file():
        return None
    try:
        integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    actual_sha = file_sha256(calib_path)
    if integrity.get("sha256") != actual_sha:
        raise ModelError("El SHA-256 del calibrador de probabilidad no coincide con el valor registrado")
    try:
        bundle = joblib.load(calib_path)
    except Exception as ex:
        raise ModelError("No se pudo cargar el artefacto del calibrador") from ex
    if isinstance(bundle, dict):
        estimator = bundle.get("estimator")
        coef = float(bundle.get("coef", manifest.get("coeficiente_sigmoide", 0.0)))
        intercept = float(bundle.get("intercept", manifest.get("intercepto_sigmoide", 0.0)))
    elif hasattr(bundle, "coef_"):
        estimator = bundle
        coef = float(bundle.coef_[0, 0])
        intercept = float(bundle.intercept_[0])
    else:
        coef = float(manifest.get("coeficiente_sigmoide", 0.0))
        intercept = float(manifest.get("intercepto_sigmoide", 0.0))
        estimator = None
    return CalibratorArtifact(estimator=estimator, coef=coef, intercept=intercept, manifest=manifest, sha256=actual_sha, path=calib_path)
