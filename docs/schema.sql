PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS ejecuciones (
    execution_id TEXT PRIMARY KEY,
    fecha_utc TEXT NOT NULL,
    nombre_csv TEXT NOT NULL,
    sha256_entrada TEXT NOT NULL,
    sha256_modelo TEXT NOT NULL,
    version_modelo TEXT NOT NULL,
    algoritmo TEXT NOT NULL,
    escenario TEXT NOT NULL,
    total_registros INTEGER NOT NULL CHECK(total_registros > 0),
    total_positivos INTEGER NOT NULL CHECK(total_positivos >= 0 AND total_positivos <= total_registros),
    tipo_score TEXT NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('INICIADA','COMPLETADA','ERROR'))
);
CREATE TABLE IF NOT EXISTS predicciones (
    execution_id TEXT NOT NULL,
    prioridad INTEGER NOT NULL CHECK(prioridad > 0),
    id_modulo TEXT NOT NULL,
    clase_predicha INTEGER NOT NULL CHECK(clase_predicha IN (0,1)),
    score_riesgo REAL NOT NULL,
    tipo_score TEXT NOT NULL,
    PRIMARY KEY (execution_id, prioridad),
    FOREIGN KEY (execution_id) REFERENCES ejecuciones(execution_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_fecha ON ejecuciones(fecha_utc DESC);
CREATE INDEX IF NOT EXISTS idx_predicciones_clase ON predicciones(clase_predicha);
