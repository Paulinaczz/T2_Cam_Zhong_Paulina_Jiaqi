import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evidencias/pi15/oe3/ejecutar_completo.py"
spec = importlib.util.spec_from_file_location("launcher_cp09", SCRIPT)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def test_cli_existing_output_requires_resume_and_preserves_bytes(tmp_path):
    sentinel = tmp_path / "resultado.csv"
    sentinel.write_bytes(b"resultado,valor\noriginal,42\n")
    before = sentinel.read_bytes()
    process = subprocess.run(
        [sys.executable, "-X", "utf8", "-B", str(SCRIPT), "--salida", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT
    )
    assert process.returncode == 2
    assert "--reanudar" in process.stderr
    assert sentinel.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == ["resultado.csv"]


def test_new_output_is_accepted_without_creating_it(tmp_path):
    folder = tmp_path / "nueva"
    launcher.check_output(folder, resume=False)
    assert not folder.exists()


def test_resume_requires_existing_metadata_and_results(tmp_path):
    with pytest.raises(ValueError, match="entorno.json"):
        launcher.check_output(tmp_path, resume=True)
    (tmp_path / "entorno.json").write_text("{}", encoding="utf-8")
    (tmp_path / "ejecucion_completa").mkdir()
    launcher.check_output(tmp_path, resume=True)


def test_resume_rejects_changed_environment_without_writing(tmp_path):
    environment = {field: "original" for field in launcher.IDENTITY_FIELDS}
    path = tmp_path / "entorno.json"
    path.write_text(json.dumps(environment), encoding="utf-8")
    original = path.read_bytes()
    launcher.validate_resume(tmp_path, environment)
    changed = {**environment, "paquetes": "otras versiones"}
    with pytest.raises(ValueError, match="paquetes"):
        launcher.validate_resume(tmp_path, changed)
    assert path.read_bytes() == original


@pytest.mark.parametrize("resume", [False, True])
def test_published_outputs_are_protected_even_with_resume(resume):
    with pytest.raises(ValueError, match="evidencias publicadas"):
        launcher.check_output(SCRIPT.parent, resume=resume)
