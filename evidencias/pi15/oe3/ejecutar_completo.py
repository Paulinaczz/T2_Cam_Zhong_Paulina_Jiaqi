"""Ejecuta Nested LOPO completo en una carpeta nueva; reanudación explícita."""
import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESOURCES = Path(__file__).resolve().parent
IDENTITY_FIELDS = (
    "python", "plataforma", "paquetes", "bibliotecas_nativas",
    "script_sha256", "artefactos_protegidos", "config_hash",
)


def check_output(folder, resume):
    folder = folder.resolve()
    for protected in (RESOURCES, ROOT / "artifacts/models"):
        if folder == protected or folder.is_relative_to(protected):
            raise ValueError("La salida debe estar fuera de los artefactos y las evidencias publicadas de OE3.")
    if not resume and folder.exists():
        raise FileExistsError("La salida ya existe. Usa una carpeta nueva o --reanudar explícitamente.")
    if resume and not ((folder / "entorno.json").is_file()
                       and (folder / "ejecucion_completa").is_dir()):
        raise ValueError("--reanudar requiere entorno.json y ejecucion_completa existentes.")


def validate_resume(folder, environment):
    saved = json.loads((folder / "entorno.json").read_text(encoding="utf-8"))
    mismatches = [field for field in IDENTITY_FIELDS if saved.get(field) != environment[field]]
    if mismatches:
        raise ValueError("Checkpoint incompatible. Cambiaron: " + ", ".join(mismatches))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, required=True, help="Directorio de trabajo nuevo.")
    parser.add_argument("--datos", type=Path, default=ROOT / "research/raw/pi14")
    parser.add_argument("--reanudar", action="store_true", help="Reutilizar checkpoints compatibles.")
    args = parser.parse_args(argv)
    folder = args.salida.resolve()
    try:
        check_output(folder, args.reanudar)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))

    sys.path.insert(0, str(ROOT))
    import pandas as pd
    from threadpoolctl import threadpool_info, threadpool_limits
    from research import entrenamiento_defectos as core

    required = (RESOURCES / "requirements_fijados.txt").read_text(encoding="utf-8-sig").splitlines()
    for line in required:
        package, pinned = line.split("==")
        if version(package) != pinned:
            parser.error(f"Versión incompatible de {package}; se requiere {pinned}.")
    if platform.python_version() != "3.13.0":
        parser.error("El entorno de referencia requiere Python 3.13.0.")
    assert core.SEED == 42 and len(core.CANDIDATES) == 27
    original, audits = core.load_all(args.datos)
    data, _, _ = core.deduplicar_global(original, seed=42)
    reference = ROOT / "research/experimentos/validacion_anidada"
    lock, _ = core.config_hash(audits, list(data), data, "deduplicado")
    assert lock == json.loads((reference / "configuracion.json").read_text())["hash"]
    assert core.overlap_audit(data).vectores_identicos.eq(0).all()
    artifacts = ROOT / "artifacts/models"
    protected = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in artifacts.iterdir() if path.is_file()
    }
    output = folder / "ejecucion_completa"
    with threadpool_limits(limits=1):
        environment = {
            "python": platform.python_version(),
            "plataforma": platform.platform(),
            "inicio_utc": datetime.now(timezone.utc).isoformat(),
            "paquetes": {line.split("==")[0]: version(line.split("==")[0]) for line in required},
            "bibliotecas_nativas": [
                {key: value for key, value in item.items() if key != "filepath"}
                for item in threadpool_info()
            ],
            "script_sha256": hashlib.sha256((ROOT / "research/entrenamiento_defectos.py").read_bytes()).hexdigest(),
            "artefactos_protegidos": protected,
            "config_hash": lock,
            "metodo": "27 candidatos completos, 5 folds externos, selección global, un hilo, semilla 42",
        }
        if args.reanudar:
            try:
                validate_resume(folder, environment)
            except ValueError as error:
                parser.error(str(error))
        else:
            folder.mkdir(parents=True, exist_ok=False)
            output.mkdir()
            (folder / "entorno.json").write_text(
                json.dumps(environment, indent=2) + "\n", encoding="utf-8"
            )
        summary = core.run_nested(data, audits, output, modo="deduplicado")

    for name in [*(f"inner_{project}.json" for project in core.PROJECTS), "seleccion_final_cv.json"]:
        checkpoint = json.loads((output / name).read_text())
        assert len(checkpoint["rows"]) == 27
        assert all(row["error"] is None and row["n_folds"] == len(checkpoint["proyectos"])
                   for row in checkpoint["rows"])
    new = pd.read_csv(output / "comparacion_algoritmos_outer.csv")
    old = pd.read_csv(reference / "comparacion_algoritmos_outer.csv")
    pairs = new.merge(
        old, on=["proyecto_test", "algoritmo"],
        suffixes=("_nuevo", "_historico"), validate="one_to_one"
    )
    for metric in ["f1", "auc_roc", "average_precision"]:
        pairs["delta_" + metric] = pairs[metric + "_nuevo"] - pairs[metric + "_historico"]
    pairs.to_csv(folder / "comparacion_historico.csv", index=False, lineterminator="\n")
    for path in artifacts.iterdir():
        if path.is_file():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == protected[path.name]
    checks = {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.rglob("*")) if path.is_file()
    }
    (folder / "sha256_salidas.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    print("NESTED LOPO COMPLETO TERMINADO", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
