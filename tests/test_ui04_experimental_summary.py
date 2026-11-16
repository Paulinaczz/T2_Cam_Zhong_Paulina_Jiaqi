import csv
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.pds.model import load_model
from src.pds.service import prepare_csv


ROOT = Path(__file__).resolve().parents[1]


def test_ui04_favorable_projects_match_experimental_csv(tmp_path, monkeypatch):
    source = (
        ROOT
        / "research/experimentos/estrategia_esfuerzo/principal_deduplicada"
        / "diferencias_20pct_LOC_por_proyecto.csv"
    )
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = {
        row["proyecto"]
        for row in rows
        if float(row["delta_ML_calibrado_por_LOC_menos_ManualUp"]) > 0
    }
    assert expected

    monkeypatch.setenv("PDS_DB_PATH", str(tmp_path / "ui04.sqlite3"))
    model = load_model(ROOT / "artifacts/models")
    sample = ROOT / "data/sample/ejemplo_carga.csv"
    app = AppTest.from_file(str(ROOT / "app.py"))
    app.session_state["entrada"] = prepare_csv(sample.read_bytes(), sample.name, model)
    app.session_state["pagina"] = "Validación"
    app.run()
    next(button for button in app.button if "Ejecutar predicción" in button.label).click().run()
    assert not app.exception
    assert not app.error

    messages = "\n".join(str(element.value) for element in app.info)
    match = re.search(
        r"La estrategia ML superó a ManualUp en \*\*(\d+) de los (\d+) proyectos\*\*\s*\(([^)]+)\)",
        messages,
    )
    assert match, messages
    displayed_projects = set(re.findall(r"[A-Z]+\d+", match.group(3)))
    assert (int(match.group(1)), int(match.group(2))) == (len(expected), len(rows))
    assert displayed_projects == expected
