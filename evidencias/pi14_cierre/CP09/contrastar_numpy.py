"""Reentrena una vez las 15 recetas archivadas con NumPy 2.1.3."""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path.cwd()))
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from research import entrenamiento_defectos as core

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--datos",type=Path,required=True)
parser.add_argument("--salida",type=Path,required=True)
args=parser.parse_args()
assert np.__version__=="2.1.3" and core.SEED==42
reference=Path("research/experimentos/validacion_anidada")
archive=pd.read_csv(reference/"comparacion_algoritmos_outer.csv")
old=pd.read_csv("evidencias/pi14_revision/A/repeticion_recetas_fijas/semilla42_a/metricas.csv")
base=archive.merge(old,on=["proyecto_test","algoritmo","escenario"],suffixes=("_historico","_numpy255"),validate="one_to_one")
raw,audits=core.load_all(args.datos)
dedup,_,_=core.deduplicar_global(raw,seed=42)
lock,_=core.config_hash(audits,list(dedup),dedup,"deduplicado")
assert lock==json.loads((reference/"configuracion.json").read_text())["hash"]
fields=("f1","auc_roc","average_precision")
with threadpool_limits(limits=1), args.salida.open("x",encoding="utf-8",newline="") as stream:
    writer=csv.DictWriter(stream,fieldnames=["proyecto","algoritmo","escenario",*[f"{m}_{s}" for m in fields for s in ("historico","numpy255","numpy213")]])
    writer.writeheader()
    for row in base.itertuples():
        target=row.proyecto_test
        x,y=core.pack(dedup,[p for p in dedup if p!=target])
        pipeline=core.make_pipeline(row.escenario,row.algoritmo)
        pipeline.fit(x,y)
        result,_,_=core.metrics(pipeline,*dedup[target])
        record={"proyecto":target,"algoritmo":row.algoritmo,"escenario":row.escenario}
        for metric in fields:
            record[f"{metric}_historico"]=getattr(row,f"{metric}_historico")
            record[f"{metric}_numpy255"]=getattr(row,f"{metric}_numpy255")
            record[f"{metric}_numpy213"]=result[metric]
        writer.writerow(record)
        stream.flush()
        print(target,row.algoritmo,flush=True)
