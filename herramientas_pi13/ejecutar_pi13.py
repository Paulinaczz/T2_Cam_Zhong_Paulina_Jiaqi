#!/usr/bin/env python3
"""Registro reproducible de CP01–CP06 y CP11–CP12 para PDS-QA.

Se ejecuta DESDE EL REPOSITORIO LOCAL, sin modificar la app ni su modelo.
Los resultados son pruebas de núcleo/backend, no sustituyen capturas de UI.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd

BASE_HERRAMIENTA = Path(__file__).resolve().parent
CASOS = {"CP01": "Importar, validar, inferir y ordenar 18 módulos",
         "CP02": "Rechazo de CSV sin métrica LOC",
         "CP03": "Rechazo de Inf y texto no numérico",
         "CP04": "Escapado de fórmulas en exportación CSV",
         "CP05": "Persistencia e historial SQLite de 18 predicciones",
         "CP06": "Rendimiento con al menos 30 repeticiones y lote JM1",
         "CP11": "Rechazo de extensión inválida e ID duplicado",
         "CP12": "Bloqueo de un modelo con SHA-256 alterado (copia)"}
CAPTURAS = {
    "CP01": [("CP01_UI02_carga.png", "UI02: carga de ejemplo_carga.csv"),
             ("CP01_UI03_validacion.png", "UI03: 18 módulos y 21 métricas"),
             ("CP01_UI04_resultados.png", "UI04: ranking de 18 módulos")],
    "CP02": [("CP02_rechazo_sin_loc.png", "UI02: rechazo del CSV sin la columna loc")],
    "CP03": [("CP03_rechazo_inf.png", "UI02: rechazo de valores Inf"),
             ("CP03_rechazo_texto.png", "UI02: rechazo de dato no numérico")],
    "CP04": [("CP04_exportacion_escapada.png", "CSV exportado abierto como texto, identificador con comilla inicial")],
    "CP05": [("CP05_UI05_historial.png", "UI05: UUID, hash y 18 registros consultables")],
    "CP06": [("CP06_equipo_y_ejecucion.png", "Consola local mostrando equipo y corrida de rendimiento")],
    "CP11": [("CP11_rechazo_id_duplicado.png", "UI02: rechazo de IDs duplicados")],
    "CP12": [("CP12_bloqueo_hash.png", "Consola: rechazo SHA-256 sobre una copia aislada")]
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def json_write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def packages():
    names = ("python", "scikit-learn", "imbalanced-learn", "pandas", "numpy", "joblib", "pytest", "streamlit")
    ans = {"python": platform.python_version()}
    for n in names[1:]:
        try: ans[n] = version(n)
        except PackageNotFoundError: ans[n] = "NO_INSTALADO"
    return ans


def git_commit(repo: Path):
    try:
        result = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else "Sin commit local verificable"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "Sin commit local verificable"


def check_repo(repo: Path):
    required = ["app.py", "src/pds/service.py", "src/pds/validation.py", "src/pds/prediction.py",
                "src/pds/model.py", "src/pds/persistence.py", "artifacts/models/metadatos_modelo.json",
                "data/sample/ejemplo_carga.csv", "docs/schema.sql"]
    miss = [x for x in required if not (repo / x).is_file()]
    if miss:
        raise RuntimeError("No se encuentra la raíz correcta del repositorio. Faltan: " + ", ".join(miss))


def imports_pds(repo: Path):
    # Mismo import que utiliza app.py, desde la RAÍZ del repositorio.
    sys.path.insert(0, str(repo))
    from src.pds.errors import InputError, ModelError
    from src.pds.model import load_model, file_sha256, ensure_compatible_versions
    from src.pds.service import prepare_csv, run_analysis
    from src.pds.prediction import predict, csv_results
    from src.pds.persistence import init_db, list_executions, get_execution
    return locals()


def prepare_fixtures(root: Path, evidencias: Path):
    src = root / "data/sample/ejemplo_carga.csv"
    df = pd.read_csv(src, dtype=str, keep_default_na=False)
    if len(df) != 18:
        raise AssertionError("El ejemplo del repositorio no tiene 18 filas; revisar el plan CP01")
    folder = evidencias / "entradas_prueba"
    folder.mkdir(parents=True, exist_ok=True)
    fixtures = {}
    def write(name, frame, ext="csv"):
        path = folder / f"{name}.{ext}"
        frame.to_csv(path, index=False, encoding="utf-8")
        fixtures[name] = path
    write("CP02_sin_loc", df.drop(columns=["loc"]))
    inf = df.copy(); inf.loc[0, "loc"] = "inf"; write("CP03_inf", inf)
    txt = df.copy(); txt.loc[0, "v"] = "VALOR_INVALIDO"; write("CP03_texto", txt)
    formulas = df.copy(); formulas.loc[0, "id_modulo"] = "=1+2"; write("CP04_formula", formulas)
    dup = df.copy(); dup.loc[1, "id_modulo"] = dup.loc[0, "id_modulo"]; write("CP11_id_duplicado", dup)
    inval = folder / "CP11_extension_invalida.xlsx"
    inval.write_bytes(src.read_bytes()); fixtures["CP11_extension_invalida"] = inval
    fixtures["CP01_original"] = src
    json_write(folder/"hashes_entradas.json", {n: {"archivo": str(p.relative_to(evidencias)) if p.is_relative_to(evidencias) else str(p), "sha256": sha256_file(p)} for n,p in fixtures.items()})
    return fixtures


class Logger:
    def __init__(self, out: Path):
        self.out = out
        self.out.mkdir(parents=True, exist_ok=True)
        prior = self.out / "registro_casos.json"
        self.records = json.loads(prior.read_text(encoding="utf-8")) if prior.is_file() else []
    def emit(self, message):
        print(message, flush=True)
        with (self.out/"ejecucion.log").open("a", encoding="utf-8") as f:
            f.write(f"{now()} | {message}\n")
    def run(self, case, fn):
        self.emit(f"INICIO {case}: {CASOS[case]}")
        started = time.perf_counter()
        try:
            info = fn()
            ok, reason, evidence = True, "Aprobado en núcleo/backend; requiere capturas UI", info
            self.emit(f"APROBADO {case} ({time.perf_counter()-started:.2f} s)")
        except Exception as ex:
            ok, reason = False, f"{type(ex).__name__}: {ex}"
            self.emit(f"FALLÓ {case}: {reason}")
            self.emit(traceback.format_exc())
            evidence = {"error": reason}
        row = {"caso": case, "escenario": "ES"+case[2:],
               "fecha_utc": now(), "estado_backend": "APROBADO_BACKEND" if ok else "FALLÓ_BACKEND",
               "evidencia": evidence, "observacion": reason,
               "captura_ui": "PENDIENTE_DE_VERIFICACION_MANUAL"}
        self.records = [old for old in self.records if old["caso"] != case]
        self.records.append(row)
        self.persist()
        return ok
    def persist(self):
        json_write(self.out/"registro_casos.json", self.records)
        path = self.out/"registro_casos_para_PI13.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["ID caso", "Escenario", "Fecha UTC", "Resultado backend", "Resultado UI", "Observación", "Evidencia JSON"])
            for r in self.records:
                w.writerow([r["caso"],r["escenario"],r["fecha_utc"],r["estado_backend"],
                            r["captura_ui"],r["observacion"],"registro_casos.json"])


def run_functional(repo: Path, out: Path, log: Logger, pds, artifact):
    prep=pds["prepare_csv"]; run=pds["run_analysis"]
    init=pds["init_db"]; history=pds["list_executions"]; get=pds["get_execution"]
    predict=pds["predict"]; csv_results=pds["csv_results"]
    InputError=pds["InputError"]; ModelError=pds["ModelError"]
    fixtures=prepare_fixtures(repo, out)
    cases=out/"casos"; cases.mkdir(parents=True,exist_ok=True)

    def cp01():
        folder=cases/"CP01"; folder.mkdir(exist_ok=True)
        blob=fixtures["CP01_original"].read_bytes()
        val=prep(blob, "ejemplo_carga.csv", artifact)
        assert val.original_rows == 18 and val.features.shape==(18,21)
        db=folder/"traza_cp01.sqlite3"; init(db)
        execution_id, pred=run(val, artifact, db)
        assert len(pred)==18 and pred["prioridad"].tolist()==list(range(1,19))
        assert pred["score_riesgo"].is_monotonic_decreasing
        assert set(pred["tipo_score"])=={"margen_svm_no_calibrado"}
        assert len(history(db))==1
        (folder/"predicciones_cp01.csv").write_bytes(csv_results(pred))
        json_write(folder/"comprobacion.json", {"registros":len(pred),"metricas":21,
                    "algoritmo":artifact.manifest["algoritmo"],"escenario":artifact.manifest["escenario"],
                    "tipo_score": pred["tipo_score"].iloc[0],"id_ejecucion":execution_id,
                    "sha256_modelo":artifact.sha256,"sha256_entrada":val.sha256,
                    "columnas_salida":list(pred.columns),"advertencias":val.warnings})
        return {"ruta":str(folder.relative_to(out)),"filas":18,"evidencia":"comprobacion.json + predicciones_cp01.csv + traza_cp01.sqlite3"}

    def reject_case(path, filename=None):
        try: prep(path.read_bytes(), filename or path.name, artifact)
        except InputError as ex: return str(ex)
        raise AssertionError("El CSV inválido fue aceptado incorrectamente")

    def cp02():
        folder=cases/"CP02"; folder.mkdir(exist_ok=True)
        db=folder/"db_control.sqlite3"; init(db)
        msg=reject_case(fixtures["CP02_sin_loc"])
        assert "loc" in msg.lower() and len(history(db))==0
        save_text(folder/"rechazo.txt",msg+"\nNo se crearon ejecuciones en SQLite.\n")
        return {"ruta":str(folder.relative_to(out)),"rechazo":msg,"ejecuciones_guardadas":0}

    def cp03():
        folder=cases/"CP03"; folder.mkdir(exist_ok=True)
        db=folder/"db_control.sqlite3"; init(db)
        msg_inf=reject_case(fixtures["CP03_inf"])
        msg_txt=reject_case(fixtures["CP03_texto"])
        assert "infinit" in msg_inf.lower() and "num" in msg_txt.lower()
        assert len(history(db))==0
        save_text(folder/"rechazos.txt", "Inf: "+msg_inf+"\nTexto: "+msg_txt+"\n")
        return {"ruta":str(folder.relative_to(out)),"inf":msg_inf,"texto":msg_txt,"ejecuciones_guardadas":0}

    def cp04():
        folder=cases/"CP04"; folder.mkdir(exist_ok=True)
        val=prep(fixtures["CP04_formula"].read_bytes(), "CP04_formula.csv", artifact)
        pred=predict(val,artifact)
        data=csv_results(pred)
        (folder/"salida_sanitizada.csv").write_bytes(data)
        parsed=pd.read_csv(folder/"salida_sanitizada.csv",dtype=str,keep_default_na=False)
        id_formula=parsed.loc[parsed.id_modulo.str.contains("1\\+2",regex=True),"id_modulo"]
        assert len(id_formula)==1 and id_formula.iloc[0]=="'=1+2"
        assert "'=1+2" in data.decode("utf-8-sig")
        json_write(folder/"comprobacion.json",{"entrada":"=1+2", "exportado":id_formula.iloc[0],
                 "advertencia":"Se comprueba la sanitización textual del CSV; no se abre Microsoft Excel ni se simulan macros."})
        return {"ruta":str(folder.relative_to(out)),"resultado":"Identificador escapado antes de exportación"}

    def cp05():
        folder=cases/"CP05"; folder.mkdir(exist_ok=True)
        blob=fixtures["CP01_original"].read_bytes()
        val=prep(blob,"ejemplo_carga.csv",artifact)
        db=folder/"traza_cp05.sqlite3"; init(db)
        eid,pred=run(val,artifact,db)
        assert str(uuid.UUID(eid))==eid
        hist=history(db); meta,saved=get(db,eid)
        assert len(hist)==1 and len(saved)==18
        assert meta["sha256_entrada"]==val.sha256 and meta["sha256_modelo"]==artifact.sha256
        assert meta["estado"]=="COMPLETADA" and meta["total_registros"]==18
        assert hist.iloc[0].execution_id==eid
        assert saved.prioridad.tolist()==list(range(1,19))
        assert sorted(saved.id_modulo.tolist())==sorted(pred.id_modulo.tolist())
        assert saved.tipo_score.nunique()==1 and saved.tipo_score.iloc[0]=="margen_svm_no_calibrado"
        hist.to_csv(folder/"historial.csv", index=False,encoding="utf-8-sig")
        saved.to_csv(folder/"predicciones_sqlite.csv", index=False,encoding="utf-8-sig")
        json_write(folder/"comprobacion.json", {"execution_id":eid,"estado":meta["estado"],
                   "filas":len(saved),"hash_entrada":meta["sha256_entrada"],
                   "hash_modelo":meta["sha256_modelo"], "base_aislada":str(db.relative_to(out))})
        return {"ruta":str(folder.relative_to(out)),"UUID":eid,"filas_sqlite":len(saved)}

    def cp11():
        folder=cases/"CP11"; folder.mkdir(exist_ok=True)
        db=folder/"db_control.sqlite3"; init(db)
        msg_ext=reject_case(fixtures["CP11_extension_invalida"])
        msg_dup=reject_case(fixtures["CP11_id_duplicado"])
        assert "extensión" in msg_ext.lower() and "repetidos" in msg_dup.lower()
        assert len(history(db))==0
        save_text(folder/"rechazos.txt","Extensión: "+msg_ext+"\nID repetido: "+msg_dup+"\n")
        return {"ruta":str(folder.relative_to(out)),"extension":msg_ext,"ids":msg_dup,"ejecuciones_guardadas":0}

    def cp12():
        folder=cases/"CP12"; folder.mkdir(exist_ok=True)
        originals=repo/"artifacts/models"
        manifest=originals/"metadatos_modelo.json"
        original_hash=pds["file_sha256"](originals/"modelo_predictivo_pds.joblib")
        with tempfile.TemporaryDirectory(prefix="pds_cp12_") as tmp:
            tmp=Path(tmp)
            # Solo se copia a una carpeta temporal: la app original no se toca.
            for f in ("metadatos_modelo.json","integridad_modelo.json","modelo_predictivo_pds.joblib"):
                shutil.copy2(originals/f,tmp/f)
            path=tmp/"integridad_modelo.json"
            integrity=json.loads(path.read_text(encoding="utf-8"))
            integrity["sha256"]="0"*64
            json_write(path,integrity)
            try: pds["load_model"](tmp)
            except ModelError as ex: msg=str(ex)
            else: raise AssertionError("El modelo con hash falso fue aceptado")
            assert "SHA-256" in msg
        assert original_hash == pds["file_sha256"](originals/"modelo_predictivo_pds.joblib")
        save_text(folder/"rechazo_hash.txt",msg+"\nHash del modelo ORIGINAL sin cambios: "+original_hash+"\n")
        json_write(folder/"comprobacion.json",{"mensaje":msg,"original_intacto":True,"sha256_modelo":original_hash,
                          "nota":"Solo se modificó una copia temporal de integridad_modelo.json."})
        return {"ruta":str(folder.relative_to(out)),"modelo_original_intacto":True,"rechazo":msg}

    for id_, fn in [("CP01",cp01),("CP02",cp02),("CP03",cp03),("CP04",cp04),
                    ("CP05",cp05),("CP11",cp11),("CP12",cp12)]:
        log.run(id_,fn)


def run_pytest(repo: Path,out: Path,log:Logger):
    log.emit("Iniciando suite existente pytest (evidencia COMPLEMENTARIA; distinta de CP01–CP12)")
    cmd=[sys.executable,"-m","pytest","-q","tests"]
    try:
        result=subprocess.run(cmd,cwd=repo,capture_output=True,text=True,timeout=600)
        text=f"COMANDO: {' '.join(cmd)}\nCÓDIGO: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n"
        save_text(out/"suite_pytest.txt",text)
        log.emit(f"Pytest finalizó con código {result.returncode}. Revisar suite_pytest.txt y posibles SKIP")
    except Exception as ex:
        save_text(out/"suite_pytest.txt",f"NO EJECUTADA: {type(ex).__name__}: {ex}\n")
        log.emit(f"Pytest no pudo ejecutarse: {ex}")


def run_performance(repo: Path,out: Path,log:Logger,pds,artifact,jm1:Path,repetitions:int):
    if repetitions<30:
        raise RuntimeError("CP06 exige al menos 30 repeticiones por lote según observación O6")
    sample=repo/"data/sample/ejemplo_carga.csv"
    if not jm1.is_file():
        raise FileNotFoundError("No se encuentra JM1; añade --jm1 ruta/JM1_para_CP06.csv")
    inputs={"ejemplo_18":sample,"JM1_completo":jm1}
    outputs=out/"casos/CP06"; outputs.mkdir(parents=True,exist_ok=True)
    progress_file=outputs/"mediciones_parciales.jsonl"
    meta_file=outputs/"configuracion.json"
    datasets={key:{"ruta":str(path.resolve()),"sha256":sha256_file(path),"filas_esperadas":18 if key=="ejemplo_18" else 13204}
              for key,path in inputs.items()}
    config={"hash_modelo":artifact.sha256,"repeticiones":repetitions,"datasets":datasets,
            "excluye_arranque":True,"sin_persistencia_en_tiempos":True}
    if meta_file.is_file():
        old=json.loads(meta_file.read_text(encoding="utf-8"))
        if old != config:
            raise RuntimeError("No puede reanudar con otro modelo/datos/repeticiones. Use nueva carpeta --salida")
    else:
        json_write(meta_file, config)
    done={}
    if progress_file.is_file():
        for line in progress_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row=json.loads(line); done[(row["lote"],row["repeticion"])]=row
    log.emit(f"CP06: ya hay {len(done)} registros guardados; se reanudará donde terminó.")
    inputs_bytes={label:p.read_bytes() for label,p in inputs.items()}
    # Calentamiento; no se contabiliza en p95 ni en media.
    for label,blob in inputs_bytes.items():
        pds["predict"](pds["prepare_csv"](blob, inputs[label].name,artifact),artifact)
        log.emit(f"CP06 calentamiento terminado: {label}")
    for label,blob in inputs_bytes.items():
        for i in range(1,repetitions+1):
            if (label,i) in done: continue
            t0=time.perf_counter()
            valid=pds["prepare_csv"](blob,inputs[label].name,artifact)
            t1=time.perf_counter()
            result=pds["predict"](valid,artifact)
            t2=time.perf_counter()
            expected=datasets[label]["filas_esperadas"]
            if valid.original_rows != expected or len(result)!=expected:
                raise AssertionError(f"{label}: esperaba {expected} filas, obtuve {len(result)}")
            row={"lote":label,"repeticion":i,"fecha_utc":now(),"n_modulos":expected,
                 "validacion_s":round(t1-t0,6),"inferencia_s":round(t2-t1,6),
                 "total_s":round(t2-t0,6)}
            with progress_file.open("a",encoding="utf-8") as f:
                f.write(json.dumps(row,ensure_ascii=False)+"\n"); f.flush()
            done[(label,i)]=row
            log.emit(f"CP06 {label}: {i}/{repetitions} | validar={row['validacion_s']:.3f}s | inferir={row['inferencia_s']:.3f}s")
    rows=list(done.values());df=pd.DataFrame(rows).sort_values(["lote","repeticion"])
    df.to_csv(outputs/"mediciones_cp06.csv",index=False,encoding="utf-8-sig")
    summaries=[]
    for label,g in df.groupby("lote"):
        for metric in ("validacion_s","inferencia_s","total_s"):
            arr=g[metric].astype(float).to_numpy()
            summaries.append({"lote":label,"metrica":metric,"n":len(arr),"media_s":float(arr.mean()),
                              "mediana_s":float(np.median(arr)),"desviacion_s":float(arr.std(ddof=1)),
                              "p95_s":float(np.percentile(arr,95)),"min_s":float(arr.min()),"max_s":float(arr.max()),
                              "meta_p95_5s_aplica":label=="ejemplo_18" and metric=="inferencia_s",
                              "cumple_meta":bool(np.percentile(arr,95)<=5) if label=="ejemplo_18" and metric=="inferencia_s" else "No aplica"})
    pd.DataFrame(summaries).to_csv(outputs/"resumen_cp06.csv", index=False,encoding="utf-8-sig")
    json_write(outputs/"resumen_cp06.json",summaries)
    return {"ruta":str(outputs.relative_to(out)),"repeticiones_por_lote":repetitions,
            "lotes":{label:datasets[label]["filas_esperadas"] for label in inputs},
            "validacion_e_inferencia_separadas":True,
            "advertencia":"p95 <=5s es criterio original solo para 18 filas. Para JM1 se reporta rendimiento descriptivo, no se inventa nueva meta."}


def manual_capture_manifest(out: Path):
    capt=out/"capturas"; capt.mkdir(parents=True,exist_ok=True)
    lines=["Capturas de pantalla reales pendientes de realizar por la tesista en Streamlit.",
           "No se generan capturas ficticias ni se considera superado el componente de interfaz.",
           "Ver GUIA_EJECUCION_PI13.md para las instrucciones paso a paso.",""]
    csvpath=out/"capturas_para_PI13.csv"
    with csvpath.open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f);writer.writerow(["ID caso","Captura esperada","Qué debe mostrar","Existe"])
        for case,items in CAPTURAS.items():
            for fn,desc in items:
                writer.writerow([case, "capturas/"+fn, desc, "Sí" if (capt/fn).is_file() else "No"])
                lines.append(f"{case} | {fn} | {desc}")
    save_text(capt/"LEEME_CAPTURAS.txt","\n".join(lines)+"\n")


def main():
    ap=argparse.ArgumentParser(description="Pruebas PI13 para PDS-QA (no modifica la app ni el modelo)")
    ap.add_argument("--repo",type=Path,default=Path.cwd(),help="Ruta raíz del proyecto PDS-QA")
    ap.add_argument("--modo",choices=["funcionales","rendimiento","todo","capturas"],default="todo")
    ap.add_argument("--repeticiones",type=int,default=30)
    ap.add_argument("--jm1",type=Path,default=BASE_HERRAMIENTA/"datos/JM1_para_CP06.csv")
    ap.add_argument("--salida",type=Path,default=None,help="Carpeta de evidencias; usar la misma para reanudar CP06")
    ap.add_argument("--sin-pytest",action="store_true")
    args=ap.parse_args()
    repo=args.repo.expanduser().resolve()
    check_repo(repo)
    if args.salida is None:
        folder=repo/"evidencias/pi13"/datetime.now().astimezone().strftime("ejecucion_%Y%m%d_%H%M%S")
    else:
        folder=args.salida.expanduser().resolve()
    folder.mkdir(parents=True,exist_ok=True)
    log=Logger(folder)
    manual_capture_manifest(folder)
    if args.modo=="capturas":
        log.emit(f"Se revisaron capturas de {folder}; ver capturas_para_PI13.csv")
        return 0
    pkg=packages()
    info={"inicio_utc":now(),"sistema_operativo":platform.platform(),"arquitectura":platform.machine(),
          "procesador":platform.processor(),"paquetes":pkg,"ruta_repositorio":str(repo),
          "git_commit":git_commit(repo),"ruta_evidencias":str(folder.resolve()),
          "ambito":"pruebas automatizadas backend; completar capturas reales de interfaz"}
    json_write(folder/"entorno.json",info)
    log.emit(f"EVIDENCIAS: {folder.resolve()}")
    log.emit(f"COMMIT: {info['git_commit']}")
    pds=imports_pds(repo)
    try:
        # Verificar las versiones ANTES de cargar un Joblib confiable del repositorio local.
        pds["ensure_compatible_versions"]()
        artifact=pds["load_model"](repo/"artifacts/models")
    except Exception as ex:
        log.emit(f"ERROR DE ENTORNO/MODELO: {type(ex).__name__}: {ex}")
        json_write(folder/"error_preparacion.json",{"tipo":type(ex).__name__,"mensaje":str(ex),"paquetes":pkg})
        return 2
    json_write(folder/"modelo_validado.json",{"algoritmo":artifact.manifest.get("algoritmo"),
             "escenario":artifact.manifest.get("escenario"),"sha256":artifact.sha256,"nombre":artifact.path.name})
    if args.modo in ("funcionales","todo"):
        run_functional(repo,folder,log,pds,artifact)
        if not args.sin_pytest: run_pytest(repo,folder,log)
    if args.modo in ("rendimiento","todo"):
        # El registro se actualiza después de cada repetición; un Ctrl+C no borra las previas.
        try:
            result=run_performance(repo,folder,log,pds,artifact,args.jm1.resolve(),args.repeticiones)
            log.records = [old for old in log.records if old["caso"] != "CP06"]
            log.records.append({"caso":"CP06","escenario":"ES06","fecha_utc":now(),
                "estado_backend":"MEDICION_EJECUTADA",
                "evidencia":result,"observacion":"Medición completa; consultar el veredicto real de p95 en resumen_cp06.csv",
                "captura_ui":"PENDIENTE_DE_VERIFICACION_MANUAL"})
            log.persist()
        except KeyboardInterrupt:
            log.emit("INTERRUMPIDO: las repeticiones previas están guardadas; ejecute otra vez con la MISMA --salida y --modo rendimiento")
            return 130
        except Exception as ex:
            log.emit(f"FALLÓ CP06: {type(ex).__name__}: {ex}")
            log.emit(traceback.format_exc())
            return 2
    manual_capture_manifest(folder)
    errors=[x for x in log.records if x["estado_backend"]=="FALLÓ_BACKEND"]
    log.emit(f"RESUMEN: {len(log.records)} casos evaluados, {len(errors)} fallidos en backend. Capturas UI pendientes hasta verificarlas.")
    log.emit("REVISAR: registro_casos_para_PI13.csv, resumen_cp06.csv, suite_pytest.txt, capturas_para_PI13.csv")
    return 1 if errors else 0


if __name__=="__main__":
    raise SystemExit(main())
