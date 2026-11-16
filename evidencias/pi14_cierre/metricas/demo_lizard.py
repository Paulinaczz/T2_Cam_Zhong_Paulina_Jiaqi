"""Demostración parcial con Lizard; no genera entradas para inferir con E6."""
import json
from importlib.metadata import version
from pathlib import Path

import lizard

source = Path(__file__).with_name("ejemplo.c")
analysis = lizard.analyze_file.analyze_source_code(source.name, source.read_text(encoding="utf-8"))
rows = [
    {"funcion": item.name, "linea_inicio": item.start_line, "linea_fin": item.end_line,
     "NLOC_lizard": item.nloc, "CCN_lizard": item.cyclomatic_complexity, "tokens_lizard": item.token_count}
    for item in analysis.function_list
]
assert [row["funcion"] for row in rows] == ["clamp_negative", "aggregate_positive"]
assert [row["CCN_lizard"] for row in rows] == [2, 2]
print(json.dumps({"version":version("lizard"),"resultados":rows,
                  "alcance":"Salida de Lizard para el ejemplo; compatibilidad con PDS-QA no demostrada."},indent=2,ensure_ascii=False))
