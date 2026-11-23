"""Diagnóstico acotado de CP09; no escribe artefactos de entrenamiento."""
import argparse
import ast
import csv
import hashlib
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import pandas as pd
from sklearn import config_context
from threadpoolctl import threadpool_limits
from research import entrenamiento_defectos as pipeline

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--datos", type=Path, required=True)
parser.add_argument("--salida", type=Path, required=True)
parser.add_argument("--notebook-original", type=Path)
parser.add_argument("--backend-alternativo", action="store_true")
args = parser.parse_args()
reference = Path("research/experimentos/validacion_anidada")
archived = json.loads((reference/"configuracion.json").read_text(encoding="utf-8"))
history = pd.read_csv(reference/"comparacion_algoritmos_outer.csv")
raw, audits = pipeline.load_all(args.datos)
data, _, cohorts = pipeline.deduplicar_global(raw, seed=42)
lock, config = pipeline.config_hash(audits, list(data), data, "deduplicado")
assert json.loads(json.dumps(config)) == archived["especificacion"] and lock == archived["hash"]
assert pipeline.overlap_audit(data).vectores_identicos.eq(0).all()

functions = (
    "standard_key", "harmonize_features", "load_project", "load_all", "pack",
    "make_pipeline", "deduplicar_global", "firma_datos", "metrics", "raw_score",
    "eval_one_candidate", "select_candidate", "inner_search", "outer_test",
)
constants = ("SEED", "FEATURES", "PROJECTS", "SCENARIOS", "ALGORITHMS", "CANDIDATES")

def signatures(source):
    nodes = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            if ast.get_docstring(node):
                node.body.pop(0)
            nodes[node.name] = ast.dump(node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in constants:
                    nodes[target.id] = ast.dump(node.value)
    return nodes

def compare_notebook(path, current):
    notebook = json.loads(path.read_text(encoding="utf-8-sig"))
    source = next("".join(cell["source"]) for cell in notebook["cells"]
                  if "def make_pipeline(" in "".join(cell["source"]))
    if source.startswith("%%writefile "):
        source = source.split("\n", 1)[1]
    previous = signatures(source)
    return {name: previous.get(name) == current[name] for name in (*functions, *constants)}

current = signatures(Path("research/entrenamiento_defectos.py").read_text(encoding="utf-8"))
same = {"notebook_repo": compare_notebook(Path("research/Entrenamiento_Prediccion_Defectos.ipynb"), current)}
if args.notebook_original:
    same["notebook_colab_PI11_PI12"] = compare_notebook(args.notebook_original, current)

folds = []
for project in data:
    rows = history[history.proyecto_test == project]
    sources = [p for p in data if p != project]
    assert all(ast.literal_eval(value) == sources for value in rows.proyectos_entrenamiento)
    assert rows.n.eq(len(data[project][0])).all() and rows.positivos.eq(int(data[project][1].sum())).all()
    checkpoint = json.loads((reference/f"inner_{project}.json").read_text(encoding="utf-8"))
    candidates = checkpoint["rows"]
    assert checkpoint["config_hash"] == lock and checkpoint["proyectos"] == sources
    assert len(candidates) == len(pipeline.CANDIDATES) == 27
    for row in rows.itertuples():
        selected = pipeline.select_candidate(
            [candidate for candidate in candidates if candidate["algoritmo"] == row.algoritmo], len(sources)
        )
        assert selected["escenario"] == row.escenario
        assert abs(selected["f1_macro"] - row.cv_f1_macro_fuente) < 1e-12
    expected_folds = [
        {"validacion": val, "entrenamiento": [p for p in sources if p != val]} for val in sources
    ]
    folds.append({"externo": project, "entrenamiento_externo": sources,
                  "n_test": len(data[project][0]), "positivos_test": int(data[project][1].sum()), "candidatos_archivados": len(candidates),
                  "internos_derivados_del_codigo": expected_folds})
    if candidates:
        for candidate in candidates:
            if not candidate.get("error"):
                assert [item["proyecto_validacion"] for item in candidate["folds"]] == sources

audit = {"sha256_configuracion_historica_y_actual": lock, "especificacion": config,
         "cohorte": cohorts, "folds": folds, "igualdad_ast": same,
         "python": platform.python_version(), "sistema": platform.system(),
         "versiones": {name: version(name) for name in ("numpy","scipy","pandas","scikit-learn","imbalanced-learn","xgboost")},
         "backend_cython_distancias": not args.backend_alternativo, "hilos": 1}

records = []
with threadpool_limits(limits=1), config_context(enable_cython_pairwise_dist=not args.backend_alternativo):
    for project, algorithm in [("CM1", "Random Forest"), ("JM1", "Random Forest"), ("PC1", "Random Forest")]:
        entry = history[(history.proyecto_test == project) & (history.algoritmo == algorithm)].iloc[0]
        sources = [p for p in data if p != project]
        features, labels = pipeline.pack(data, sources)
        fit = pipeline.make_pipeline(entry.escenario, algorithm)
        print(project, algorithm, entry.escenario, flush=True)
        fit.fit(features, labels)
        metrics, _, _ = pipeline.metrics(fit, *data[project])
        record = {"proyecto": project, "algoritmo": algorithm, "escenario": entry.escenario}
        for metric in ("f1", "auc_roc", "average_precision"):
            record[metric] = float(metrics[metric])
            record[f"historico_{metric}"] = float(entry[metric])
        records.append(record)
args.salida.mkdir(parents=True, exist_ok=False)
(args.salida/"control.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
with (args.salida/"metricas.csv").open("w",encoding="utf-8",newline="") as stream:
    writer=csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
