"""M02: orquestación sin mezclar interfaz, predicción y persistencia."""
from __future__ import annotations
from pathlib import Path
from .model import load_model, ModelArtifact
from .validation import read_csv_bytes, validate_input, ValidatedInput
from .prediction import predict
from .persistence import register_execution


def prepare_csv(contents: bytes, filename: str, artifact: ModelArtifact) -> ValidatedInput:
    frame = read_csv_bytes(contents, filename)
    return validate_input(frame, list(artifact.manifest["columnas"]), contents, filename)


def run_analysis(data: ValidatedInput, artifact: ModelArtifact, db_path: Path):
    results = predict(data, artifact)
    execution_id = register_execution(db_path, data, artifact, results)
    return execution_id, results
