"""Traza dos recetas externas de CP09, sin alterar los datos ni modelos históricos."""
import argparse
import hashlib
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path.cwd()))
import numpy as np
import pandas as pd
from sklearn import config_context
from sklearn.neighbors import NearestNeighbors
from threadpoolctl import threadpool_info, threadpool_limits
from research import entrenamiento_defectos as experiment

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--datos", type=Path, required=True)
parser.add_argument("--salida", type=Path, required=True)
parser.add_argument("--variante", choices=("base","backend","empates","hilos2","numpy","scipy"), required=True)
args=parser.parse_args()
config=json.loads(Path("research/experimentos/validacion_anidada/configuracion.json").read_text())
raw,audits=experiment.load_all(args.datos)
data,_,_=experiment.deduplicar_global(raw,seed=42)
lock,_=experiment.config_hash(audits,list(data),data,"deduplicado")
assert lock==config["hash"] and experiment.SEED==42
history=pd.read_csv("research/experimentos/validacion_anidada/comparacion_algoritmos_outer.csv")
threads=2 if args.variante=="hilos2" else 1
backend=args.variante!="backend"
assert (args.variante=="numpy") == (np.__version__=="2.1.3")
assert (args.variante=="scipy") == (version("scipy")=="1.16.3")

def digest(values):
    array=np.asarray(values)
    canonical=np.ascontiguousarray(array.astype(array.dtype.newbyteorder("<"),copy=False))
    return {"shape":list(canonical.shape),"tipo":canonical.dtype.str,
            "sha256":hashlib.sha256(canonical.tobytes()).hexdigest()}

def record_pair(x,y):
    return {"x":digest(x),"y":digest(y)}

def trace(project, algorithm, scenario):
    sources=[p for p in data if p!=project]
    x,y=experiment.pack(data,sources)
    test,y_test=data[project]
    pipe=experiment.make_pipeline(scenario,algorithm)
    stages={"01_entrada":{item["proyecto"]:item["sha256"] for item in audits},
            "02_filas":{p:record_pair(*item) for p,item in data.items()},
            "03_particion":{"fuentes":sources,"train":record_pair(x,y),"test":record_pair(test,y_test)}}

    train=x
    evaluation=test
    for index, name in enumerate(("imputer","scaler","selection"),start=4):
        transformer=pipe.named_steps[name]
        if isinstance(transformer,str) and transformer=="passthrough":
            continue
        train=transformer.fit_transform(train,y)
        evaluation=transformer.transform(evaluation)
        stage={"train":digest(train),"test":digest(evaluation)}
        if name=="selection":
            stage["columnas"]=[column for column,keep in zip(x.columns,transformer.get_support()) if keep]
        stages[f"0{index}_{name}"]=stage

    neighbors=[]
    kneighbors=NearestNeighbors.kneighbors
    def traced(estimator, query=None, n_neighbors=None, return_distance=True):
        assert query is not None and not return_distance
        indices=kneighbors(estimator,query,n_neighbors,return_distance=False)
        squares=np.sum((np.asarray(query)[:,None,:]-estimator._fit_X[indices])**2,axis=2)
        known_ties=np.any(np.diff(np.sort(squares,axis=1),axis=1)==0,axis=1)
        effective=indices
        if args.variante=="empates":
            effective=indices.copy()
            # Canonicaliza empates exactos dentro de los vecinos ya devueltos.
            # No recupera otros candidatos empatados que quedaron fuera del k.
            for row in np.flatnonzero(known_ties):
                for distance in np.unique(squares[row]):
                    positions=np.flatnonzero(squares[row]==distance)
                    if len(positions)>1:
                        effective[row,positions]=np.sort(effective[row,positions])
        neighbors.append({"metodo":estimator._fit_method,"indices":digest(effective),
             "conjunto_por_fila":digest(np.sort(effective,axis=1)),
             "filas_con_empate_exacto_dentro_de_k":int(known_ties.sum()),
             "filas_reordenadas_en_variante":int(np.any(indices!=effective,axis=1).sum())})
        return effective

    with patch.object(NearestNeighbors,"kneighbors",traced):
        balanced,balanced_y=pipe.named_steps["sampler"].fit_resample(train,y)
    assert len(neighbors)==2
    stages["07_vecinos_globales"]=neighbors[0]
    stages["08_vecinos_minoritarios"]=neighbors[1]
    stages["09_muestras_ADASYN"]=record_pair(balanced[len(train):],balanced_y[len(train):])
    assert np.array_equal(balanced[:len(train)],train)
    pipe.named_steps["model"].fit(balanced,balanced_y)
    metrics,scores,labels=experiment.metrics(pipe,test,y_test)
    stages["10_margen_o_score"]=digest(scores)
    stages["11_predicciones"]=digest(labels)
    reference=history[(history.proyecto_test==project)&(history.algoritmo==algorithm)].iloc[0]
    assert scenario==reference.escenario
    keys=["f1","auc_roc","average_precision"]
    return {"proyecto":project,"algoritmo":algorithm,"escenario":scenario,"etapas":stages,
            "local":{k:metrics[k] for k in keys},"historico_agregado":{k:float(reference[k]) for k in keys}}

report={"variante":args.variante,"config_historica":lock,"python":platform.python_version(),
        "sistema":platform.system(),
        "versiones":{name:version(name) for name in ("numpy","scipy","pandas","scikit-learn","imbalanced-learn","xgboost")},
        "hilos":threads,"backend_cython":backend}
with threadpool_limits(limits=threads), config_context(enable_cython_pairwise_dist=backend):
    report["bibliotecas_nativas"]=[{k:v for k,v in item.items() if k!="filepath"} for item in threadpool_info()]
    report["casos"]=[]
    for case in (("PC1","Random Forest","E2_ADASYN"),("KC1","SVM","E6_ADASYN_MI")):
        print(args.variante,*case,flush=True)
        report["casos"].append(trace(*case))
args.salida.parent.mkdir(parents=True,exist_ok=True)
with args.salida.open("x",encoding="utf-8") as stream:
    json.dump(report,stream,indent=2,ensure_ascii=False)
    stream.write("\n")
