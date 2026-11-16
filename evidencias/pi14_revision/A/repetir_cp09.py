"""CP09. Ejecutar desde la raíz del repositorio; salidas aisladas por modo."""
import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))
import pandas as pd
from threadpoolctl import threadpool_limits
from research import entrenamiento_defectos as pipeline

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--datos", type=Path, required=True)
parser.add_argument("--salida", type=Path, required=True)
parser.add_argument("--nested-completo", action="store_true")
args = parser.parse_args()
out = args.salida.resolve()
if out.is_relative_to(Path("artifacts").resolve()) or out.is_relative_to(Path("evidencias/pi13").resolve()):
    parser.error("Usa una carpeta aislada para CP09.")
out.mkdir(parents=True, exist_ok=False)

config = json.loads(Path("research/experimentos/validacion_anidada/configuracion.json").read_text())["especificacion"]
versions = {p: version(p) for p in ("scikit-learn", "imbalanced-learn", "xgboost", "numpy", "scipy", "pandas", "joblib", "threadpoolctl")}
for package, expected in config["librerias"].items():
    assert versions[package] == expected, package

original, audits = pipeline.load_all(args.datos)
sources = {a["proyecto"]: a["sha256"] for a in audits}
assert sources == config["datasets"]
seed_data = config["seed"]
data, _, _ = pipeline.deduplicar_global(original, seed=seed_data)
assert pipeline.firma_datos(data) == config["huella_datos_procesados"]
historical = pd.read_csv("research/experimentos/validacion_anidada/comparacion_algoritmos_outer.csv")
metrics = ["f1", "auc_roc", "average_precision"]
columns = ["proyecto_test", "algoritmo", "escenario", *metrics]
environment = {"python": platform.python_version(), "sistema": platform.system(),
               "paquetes": versions, "sha256_datasets": sources, "semilla_deduplicacion": seed_data,
               "huella_cohorte": pipeline.firma_datos(data), "hilos": 1, "nested_completo": args.nested_completo}
(out/"entorno.json").write_text(json.dumps(environment, indent=2)+"\n", encoding="utf-8")

runs = {}
hashes = {}
with threadpool_limits(limits=1):
    for name, seed in (("semilla42_a",42), ("semilla42_b",42), ("semilla43",43)):
        pipeline.SEED = seed
        target = out / name
        target.mkdir()
        print(f"{name}: seed={seed}", flush=True)
        if args.nested_completo:
            pipeline.run_nested(data, audits, target, modo="deduplicado")
            table = pd.read_csv(target/"comparacion_algoritmos_outer.csv")[columns]
        else:
            rows = []
            for recipe in historical.to_dict("records"):
                project = recipe["proyecto_test"]
                X_train, y_train = pipeline.pack(data, [p for p in data if p != project])
                X_test, y_test = data[project]
                model = pipeline.make_pipeline(recipe["escenario"], recipe["algoritmo"])
                print(f"  {project} | {recipe['algoritmo']} | {recipe['escenario']}", flush=True)
                model.fit(X_train, y_train)
                result, _, _ = pipeline.metrics(model, X_test, y_test)
                rows.append({**{key: recipe[key] for key in columns[:3]}, **{key: result[key] for key in metrics}})
            table = pd.DataFrame(rows, columns=columns)
        table = table.sort_values(columns[:2]).reset_index(drop=True)
        table.to_csv(target/"metricas.csv", index=False, lineterminator="\n")
        runs[name] = table
        hashes[name] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(target.iterdir()) if p.is_file()}
        (out/"sha256.json").write_text(json.dumps(hashes,indent=2)+"\n",encoding="utf-8")

baseline = runs["semilla42_a"]
diffs = []
for name, table in runs.items():
    if name == "semilla42_a":
        continue
    paired = baseline.merge(table, on=columns[:2], suffixes=("_ref","_rep"), validate="one_to_one")
    for metric in metrics:
        paired[f"delta_{metric}"] = paired[f"{metric}_rep"]-paired[f"{metric}_ref"]
    paired["comparacion"] = name
    diffs.append(paired)
pd.concat(diffs,ignore_index=True).to_csv(out/"diferencias.csv",index=False,lineterminator="\n")
print("Igualdad exacta de métricas, semilla fija:", hashes["semilla42_a"]["metricas.csv"] == hashes["semilla42_b"]["metricas.csv"], flush=True)
