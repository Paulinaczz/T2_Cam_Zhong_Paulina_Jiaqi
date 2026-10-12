"""M08: trazabilidad mínima mediante transacciones SQLite y consultas parametrizadas."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import pandas as pd
from .errors import PersistenceError
from .model import ModelArtifact
from .validation import ValidatedInput
from .prediction import SCORE_TYPE

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "docs" / "schema.sql"


def _connect(path: Path):
    db = sqlite3.connect(str(path), timeout=10)
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db(path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _connect(path) as db:
            db.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    except (sqlite3.Error, OSError) as ex:
        raise PersistenceError("No se pudo inicializar la base de datos") from ex


def register_execution(db_path: Path, data: ValidatedInput, artifact: ModelArtifact, results: pd.DataFrame) -> str:
    if len(results) != data.original_rows:
        raise PersistenceError("No se pueden registrar resultados incompletos")
    execution_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    version = artifact.manifest.get("protocolo", "desconocido")
    rows = [
        (execution_id, int(row.prioridad), str(row.id_modulo), int(row.clase_predicha),
         float(row.score_riesgo), str(row.tipo_score))
        for row in results.itertuples(index=False)
    ]
    try:
        with _connect(Path(db_path)) as db:
            db.execute("""INSERT INTO ejecuciones
                (execution_id, fecha_utc, nombre_csv, sha256_entrada, sha256_modelo,
                version_modelo, algoritmo, escenario, total_registros, total_positivos,
                tipo_score, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (execution_id, now, data.source_name, data.sha256, artifact.sha256,
                 version, artifact.manifest.get("algoritmo"), artifact.manifest.get("escenario"),
                 data.original_rows, int((results["clase_predicha"] == 1).sum()), SCORE_TYPE, "COMPLETADA"))
            db.executemany("""INSERT INTO predicciones
                (execution_id, prioridad, id_modulo, clase_predicha, score_riesgo, tipo_score)
                VALUES (?,?,?,?,?,?)""", rows)
    except sqlite3.Error as ex:
        raise PersistenceError("No fue posible registrar la ejecución; no se guardó ningún resultado parcial") from ex
    return execution_id


def list_executions(db_path: Path, limit: int = 100) -> pd.DataFrame:
    with _connect(Path(db_path)) as db:
        return pd.read_sql_query("""SELECT execution_id, fecha_utc, nombre_csv, total_registros,
          total_positivos, algoritmo, escenario, estado, sha256_entrada, sha256_modelo,
          version_modelo, tipo_score FROM ejecuciones ORDER BY fecha_utc DESC LIMIT ?""",
          db, params=(int(limit),))


def get_execution(db_path: Path, execution_id: str) -> tuple[dict | None, pd.DataFrame]:
    with _connect(Path(db_path)) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM ejecuciones WHERE execution_id = ?", (execution_id,)).fetchone()
        records = pd.read_sql_query("""SELECT prioridad, id_modulo, clase_predicha, score_riesgo, tipo_score
            FROM predicciones WHERE execution_id = ? ORDER BY prioridad""", db, params=(execution_id,))
    return (dict(row) if row is not None else None), records
