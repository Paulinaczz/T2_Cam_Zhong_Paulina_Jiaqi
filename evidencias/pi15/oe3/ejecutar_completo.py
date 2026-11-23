"""Nested LOPO completo con 27 candidatos, secuencial y reanudable."""
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import pandas as pd
from threadpoolctl import threadpool_info, threadpool_limits
from research import entrenamiento_defectos as core

folder=Path(__file__).resolve().parent
output=folder/"ejecucion_completa"
output.mkdir(exist_ok=True)
required=(folder/"requirements_fijados.txt").read_text(encoding="utf-8-sig").splitlines()
for line in required:
    package, pinned=line.split("==")
    assert version(package)==pinned,package
assert platform.python_version()=="3.13.0"
assert core.SEED==42 and len(core.CANDIDATES)==27
original,audits=core.load_all("research/raw/pi14")
data,_,_=core.deduplicar_global(original,seed=42)
reference=Path("research/experimentos/validacion_anidada")
lock,_=core.config_hash(audits,list(data),data,"deduplicado")
assert lock==json.loads((reference/"configuracion.json").read_text())["hash"]
assert core.overlap_audit(data).vectores_identicos.eq(0).all()
artifacts=Path("artifacts/models")
protected={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts.iterdir() if p.is_file()}
with threadpool_limits(limits=1):
    environment={
        "python":platform.python_version(),"plataforma":platform.platform(),
        "inicio_utc":datetime.now(timezone.utc).isoformat(),
        "paquetes":{line.split("==")[0]:version(line.split("==")[0]) for line in required},
        "bibliotecas_nativas":[{k:v for k,v in item.items() if k!="filepath"} for item in threadpool_info()],
        "script_sha256":hashlib.sha256(Path("research/entrenamiento_defectos.py").read_bytes()).hexdigest(),
        "artefactos_protegidos":protected,"config_hash":lock,
        "metodo":"27 candidatos completos, 5 folds externos, selección global, un hilo, semilla 42"}
    (folder/"entorno.json").write_text(json.dumps(environment,indent=2)+"\n",encoding="utf-8")
    summary=core.run_nested(data,audits,output,modo="deduplicado")
for name in [*(f"inner_{project}.json" for project in core.PROJECTS), "seleccion_final_cv.json"]:
    checkpoint=json.loads((output/name).read_text())
    assert len(checkpoint["rows"])==27
    assert all(row["error"] is None and row["n_folds"]==len(checkpoint["proyectos"]) for row in checkpoint["rows"])
new=pd.read_csv(output/"comparacion_algoritmos_outer.csv")
old=pd.read_csv(reference/"comparacion_algoritmos_outer.csv")
pairs=new.merge(old,on=["proyecto_test","algoritmo"],suffixes=("_nuevo","_historico"),validate="one_to_one")
for metric in ["f1","auc_roc","average_precision"]:
    pairs["delta_"+metric]=pairs[metric+"_nuevo"]-pairs[metric+"_historico"]
pairs.to_csv(folder/"comparacion_historico.csv",index=False,lineterminator="\n")
for path in artifacts.iterdir():
    if path.is_file():
        assert hashlib.sha256(path.read_bytes()).hexdigest()==protected[path.name]
checks={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.rglob("*")) if p.is_file()}
(folder/"sha256_salidas.json").write_text(json.dumps(checks,indent=2)+"\n",encoding="utf-8")
print("NESTED LOPO COMPLETO TERMINADO",json.dumps(summary),flush=True)
