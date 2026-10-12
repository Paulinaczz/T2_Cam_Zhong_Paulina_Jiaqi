"""M03: lectura segura y validación del esquema de 21 métricas NASA/PROMISE."""
from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
import hashlib
import re
import numpy as np
import pandas as pd
from .errors import InputError

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 20000
IDENTIFIER = "id_modulo"
LABEL_COLUMNS = {"defects", "problems"}  # Nunca se usan para inferencia.
ALIASES = {"locodeandcomment": "loccodeandcomment"}


@dataclass
class ValidatedInput:
    features: pd.DataFrame
    identifiers: pd.Series
    sha256: str
    original_rows: int
    source_name: str
    warnings: list[str]


def canonical_key(value: object) -> str:
    return re.sub(r"\s+", "", str(value).strip()).casefold()


def read_csv_bytes(content: bytes, filename: str) -> pd.DataFrame:
    if not filename.lower().endswith(".csv"):
        raise InputError("Solo se permiten archivos con extensión .csv")
    if not content:
        raise InputError("El archivo está vacío")
    if len(content) > MAX_BYTES:
        raise InputError("El CSV supera el límite de 10 MB")
    try:
        # Unicode-sig permite CSV con BOM exportados desde Excel; ';' se autodetecta.
        frame = pd.read_csv(BytesIO(content), sep=None, engine="python", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    except (UnicodeError, pd.errors.ParserError, ValueError, OSError) as ex:
        raise InputError("No se pudo leer el CSV. Utiliza UTF-8, encabezados y separador coma o punto y coma") from ex
    if frame.empty:
        raise InputError("El CSV debe contener al menos un registro")
    if len(frame) > MAX_ROWS:
        raise InputError(f"El CSV tiene demasiados registros (máximo {MAX_ROWS:,})")
    # pandas puede renombrar silenciosamente encabezados duplicados como .1.
    if any(re.search(r"\.\d+$", str(c)) for c in frame.columns):
        raise InputError("Se detectaron encabezados duplicados o nombres terminados en .1, .2…")
    return frame


def validate_input(raw: pd.DataFrame, expected_columns: list[str], content: bytes | None = None,
                   source_name: str = "entrada.csv") -> ValidatedInput:
    if raw.empty or len(raw) > MAX_ROWS:
        raise InputError("No hay registros válidos o se supera el límite de filas")
    if len(expected_columns) != 21 or len(set(expected_columns)) != 21:
        raise InputError("Esquema de modelo incompatible: se esperan 21 métricas")
    lookup = {}
    warnings = []
    for name in raw.columns:
        key = canonical_key(name)
        key = ALIASES.get(key, key)
        if key in lookup:
            raise InputError(f"Hay columnas duplicadas tras la normalización: '{lookup[key]}' y '{name}'")
        lookup[key] = name

    expected_map = {canonical_key(c): c for c in expected_columns}
    missing = [c for c in expected_columns if canonical_key(c) not in lookup]
    optional = {IDENTIFIER, *LABEL_COLUMNS}
    extras = [c for k, c in lookup.items() if k not in expected_map and k not in optional]
    if missing:
        raise InputError("Faltan métricas obligatorias: " + ", ".join(missing))
    if extras:
        raise InputError("Columnas no admitidas: " + ", ".join(map(str, extras)) + ". Solo las 21 métricas e id_modulo son predictoras/identificador")

    labels_found = [lookup[x] for x in LABEL_COLUMNS if x in lookup]
    if labels_found:
        warnings.append("Se excluyeron las etiquetas históricas del CSV (" + ", ".join(labels_found) + "); no se utilizan como predictores")

    if IDENTIFIER in lookup:
        ids = raw[lookup[IDENTIFIER]].astype(str).str.strip().reset_index(drop=True)
        if ids.eq("").any() or ids.duplicated().any():
            raise InputError("id_modulo no debe contener valores vacíos ni repetidos")
        if ids.str.len().gt(120).any():
            raise InputError("id_modulo admite como máximo 120 caracteres")
    else:
        ids = pd.Series([f"modulo_{i:05d}" for i in range(1, len(raw) + 1)], name=IDENTIFIER)
        warnings.append("No se proporcionó id_modulo: se generaron identificadores secuenciales")

    result = pd.DataFrame(index=range(len(raw)))
    for key, canonical in expected_map.items():
        orig = lookup[key]
        values = raw[orig].astype(str).str.strip().replace({"": np.nan, "?": np.nan, "NA": np.nan, "NaN": np.nan})
        numbers = pd.to_numeric(values, errors="coerce")
        invalid = values.notna() & numbers.isna()
        if invalid.any():
            sample = (invalid[invalid].index[:4] + 2).tolist()
            raise InputError(f"'{orig}' contiene valores no numéricos (líneas CSV: {sample})")
        if np.isinf(numbers.to_numpy(dtype=float, na_value=np.nan)).any():
            raise InputError(f"'{orig}' contiene valores infinitos")
        if numbers.isna().all():
            raise InputError(f"'{orig}' está completamente vacía: no es una entrada útil para inferencia")
        result[canonical] = numbers.astype(float).to_numpy()
        if not result[canonical].notna().all():
            warnings.append(f"'{canonical}' contiene {int(result[canonical].isna().sum())} valores faltantes; el pipeline aplicará su imputación")
    if any(c != lookup[canonical_key(c)] for c in expected_columns):
        warnings.append("Se normalizaron variantes de escritura de los nombres de métricas")
    if content is None:
        content = raw.to_csv(index=False).encode("utf-8")
    return ValidatedInput(result, ids, hashlib.sha256(content).hexdigest(), len(raw), source_name, warnings)
