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
class ModelArtifact:
    pipeline: object
    manifest: dict
    sha256: str
    path: Path


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
    if manifest_file.get("algoritmo") != "SVM" or manifest_file.get("escenario") != "E7_SMOTE_RF":
        raise ModelError("No se reconoce la configuración del modelo esperado")
    if not hasattr(pipeline, "predict") or not hasattr(pipeline, "decision_function"):
        raise ModelError("El modelo no implementa los métodos de predicción necesarios")
    # Verificación de las capas para no reutilizar solo el clasificador.
    steps = getattr(pipeline, "named_steps", {})
    if not all(k in steps for k in ("imputer", "scaler", "selection", "sampler", "model")):
        raise ModelError("Faltan transformaciones del pipeline original")
    return ModelArtifact(pipeline=pipeline, manifest=manifest_file, sha256=actual_sha, path=model_path)
