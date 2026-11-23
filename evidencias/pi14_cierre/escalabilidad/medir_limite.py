"""Mide el flujo comparativo del PR con 20 000 filas sintéticas."""
import argparse
import csv
import hashlib
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path.cwd()))
import numpy as np
import pandas as pd
import ctypes
import os
from threadpoolctl import threadpool_info
from src.pds.model import load_model
from src.pds.prediction import csv_comparison_results
from src.pds.service import prepare_csv, run_strategy_comparison
from src.pds.validation import MAX_BYTES, MAX_ROWS

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--salida", type=Path, required=True)
args = parser.parse_args()
out = args.salida
out.mkdir(parents=True, exist_ok=False)
artifact = load_model(Path("artifacts/models"))
assert artifact.calibrator is not None
sample = pd.read_csv("data/sample/ejemplo_carga.csv")
assert MAX_ROWS == 20000 and len(sample) == 18
frame = sample.iloc[np.arange(MAX_ROWS) % len(sample)].reset_index(drop=True)
frame["id_modulo"] = [f"sintetico_{i:05}" for i in range(MAX_ROWS)]
content = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
assert 0 < len(content) <= MAX_BYTES
(out/"entrada_sintetica.csv").write_bytes(content)
class MemoryStatus(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong) for name in
        ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")
    ]

memory = MemoryStatus()
memory.length = ctypes.sizeof(memory)
ram = memory.total if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)) else None
meta = {
    "filas":len(frame), "bytes":len(content), "sha256":hashlib.sha256(content).hexdigest(),
    "perfiles_repetidos":len(sample), "python":platform.python_version(),
    "sistema":platform.platform(), "cpu":platform.processor(),
    "procesadores_logicos":os.cpu_count(),
    "ram_bytes":ram,
    "versiones":{p:version(p) for p in ("numpy","pandas","scipy","scikit-learn","imbalanced-learn")},
    "bibliotecas_nativas":[{k:v for k,v in entry.items() if k!="filepath"} for entry in threadpool_info()],
    "e6_sha256":artifact.sha256,"calibrador_sha256":artifact.calibrator.sha256,
}
(out/"entorno.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
records = []
fields = ["repeticion","validacion_s","comparacion_s","exportacion_s","total_s"]
with (out/"mediciones.csv").open("w",newline="",encoding="utf-8") as stream:
    writer = csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader()
    for rep in range(1,31):
        start=perf_counter()
        valid=prepare_csv(content,"entrada_sintetica.csv",artifact)
        validated=perf_counter()
        comparison=run_strategy_comparison(valid,artifact)
        compared=perf_counter()
        exported=csv_comparison_results(comparison)
        end=perf_counter()
        assert valid.features.shape==(MAX_ROWS,21) and len(comparison)==MAX_ROWS and exported
        record=dict(zip(fields,(rep,validated-start,compared-validated,end-compared,end-start)))
        writer.writerow(record)
        stream.flush()
        records.append(record)
        print(f"{rep}/30: {record['total_s']:.3f} s",flush=True)
summary={}
for phase in fields[1:]:
    values=np.array([row[phase] for row in records])
    summary[phase]={"n":len(values),"mediana":float(np.median(values)),
                    "p95":float(np.quantile(values,.95)),"desviacion_muestral":float(values.std(ddof=1))}
(out/"resumen.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
