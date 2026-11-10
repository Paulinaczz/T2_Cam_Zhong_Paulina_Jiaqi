"""PDS tesis — validación ENTRE proyectos NASA/PROMISE, nueva ejecución completamente independiente.

Experimento educativo auditable: no es garantía de defectos de un proyecto nuevo.
Únicamente métricas históricas compatibles, no extrae código fuente.
"""
from __future__ import annotations
import hashlib, json, os, platform, sys, time
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from importlib.metadata import version
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, mutual_info_classif, SelectFromModel
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (f1_score, recall_score, precision_score, accuracy_score,
    average_precision_score, roc_auc_score, confusion_matrix)
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE, ADASYN
from xgboost import XGBClassifier
import joblib

SEED = 42
EXPERIMENT_VERSION = 'CPDP_T2_ESTUDIO_QA'
PROJECTS = ('CM1','JM1','KC1','KC2','PC1')
LABELS = {'CM1':'defects','JM1':'defects','KC1':'defects','KC2':'problems','PC1':'defects'}
SOURCE_BASE = 'https://raw.githubusercontent.com/ApoorvaKrisna/NASA-promise-dataset-repository/main'
# Orden de las 21 métricas; preservado en la exportación e inferencia. Se valida antes de unir.
FEATURES = (
    'loc','v(g)','ev(g)','iv(g)','n','v','l','d','i','e','b','t',
    'lOCode','lOComment','lOBlank','locCodeAndComment',
    'uniq_Op','uniq_Opnd','total_Op','total_Opnd','branchCount'
)
# Alias explícito a documentar. OJO: no implica equivalencia verificada por el autor.
ALIASES = {'locodeandcomment':'loccodeandcomment'}
SCENARIOS = (
    ('E0_BASELINE','NONE','NONE'),
    ('E1_SMOTE','SMOTE','NONE'),
    ('E2_ADASYN','ADASYN','NONE'),
    ('E3_MI','NONE','MI'),
    ('E4_RF_FS','NONE','RF'),
    ('E5_SMOTE_MI','SMOTE','MI'),
    ('E6_ADASYN_MI','ADASYN','MI'),
    ('E7_SMOTE_RF','SMOTE','RF'),
    ('E8_ADASYN_RF','ADASYN','RF'),
)
ALGORITHMS = ('SVM','Random Forest','XGBoost')
CANDIDATES = tuple((s[0],a) for s in SCENARIOS for a in ALGORITHMS)


def sha256(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()


def jdump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,
        default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),encoding='utf-8')
    os.replace(tmp,path)


def standard_key(s):
    return str(s).strip().casefold()


def harmonize_features(raw,project,*, allow_extra=False):
    """Mapeo verificable por encabezados, nunca descartar columnas silenciosamente."""
    raw=raw.copy()
    found={}; alias_logs=[]
    for col in raw.columns:
        k=standard_key(col)
        if k in ALIASES:
            alias_logs.append({'proyecto':project,'columna_original':str(col),
                'equivalencia_propuesta':'locCodeAndComment','pendiente_verificacion_documental':True})
            k=ALIASES[k]
        if k in found:
            raise ValueError(f'{project}: colisión tras normalizar columnas {found[k]} y {col}')
        found[k]=col
    desired={standard_key(x):x for x in FEATURES}
    missing=sorted(set(desired)-set(found))
    extras=sorted(set(found)-set(desired))
    if missing or (extras and not allow_extra):
        raise ValueError(f'{project}: esquema incompatible: faltantes={missing}, extras={extras}')
    out=pd.DataFrame(index=raw.index)
    for norm,canonical in desired.items():
        vals=raw[found[norm]].replace(['?','NA','NaN',''],np.nan)
        num=pd.to_numeric(vals,errors='coerce')
        invalid=vals.notna() & num.isna()
        if invalid.any():
            raise ValueError(f'{project}: caracteres no numéricos en {found[norm]}')
        if np.isinf(num.to_numpy(dtype=float,na_value=np.nan)).any():
            raise ValueError(f'{project}: valores infinitos en {found[norm]}')
        out[canonical]=num.astype(float)
    if out.empty: raise ValueError(f'{project}: dataset vacío')
    return out,alias_logs


def load_project(path,name):
    """Solo admite etiqueta histórica conocida por proyecto y 21 métricas esperadas."""
    if name not in PROJECTS: raise ValueError(name)
    raw=pd.read_csv(path,low_memory=False)
    if raw.empty or raw.columns.duplicated().any(): raise ValueError(f'{name}: CSV vacío o cabeceras repetidas')
    cols=[c for c in raw if standard_key(c)==LABELS[name]]
    if len(cols)!=1: raise ValueError(f'{name}: etiqueta esperada={LABELS[name]}, detectadas={list(raw.columns)}')
    target=cols[0]
    labels=raw[target].astype('string').str.strip().str.casefold()
    mapping={'false':0,'true':1,'0':0,'1':1,'0.0':0,'1.0':1,'no':0,'yes':1}
    unexpected=sorted(set(labels.dropna())-set(mapping))
    if unexpected or labels.isna().any():
        raise ValueError(f'{name}: valores de etiqueta desconocidos={unexpected}')
    y=labels.map(mapping).astype(int).reset_index(drop=True)
    if y.nunique()!=2: raise ValueError(f'{name}: se necesitan ambas clases')
    X,alias_logs=harmonize_features(raw.drop(columns=[target]),name)
    X=X.reset_index(drop=True)
    fingerprint=pd.util.hash_pandas_object(X,index=False)
    audit={'proyecto':name,'filas':len(y),'positivos':int(y.sum()),'negativos':int((y==0).sum()),
        'prevalencia':float(y.mean()),'variables':len(FEATURES),
        'etiqueta_original':target,'etiqueta_binaria':'1=defecto_historico_registrado',
        'sha256':sha256(path),'duplicados_fila_completa':int(raw.duplicated().sum()),
        'duplicados_vector_caracteristicas':int(fingerprint.duplicated().sum()),
        'faltantes':int(X.isna().sum().sum()),'alias_pendientes':alias_logs,
        'columnas_originales':list(map(str,raw.columns)),
        'procedencia_declarada':f'{SOURCE_BASE}/{name.lower()}.csv',
        'verificacion_documental_realizada':False}
    return X,y,audit


def load_all(raw_dir,names=PROJECTS):
    data={};audits=[]
    for name in names:
        p=Path(raw_dir)/f'{name}.csv'
        if not p.exists(): raise FileNotFoundError(f'{name}: falta {p}')
        x,y,a=load_project(p,name)
        data[name]=(x,y)
        audits.append(a)
    return data,audits


def overlap_audit(data):
    hashes={};pairs=[]
    for p,(x,y) in data.items():
        hashes[p]=pd.util.hash_pandas_object(x,index=False).to_numpy(dtype=np.uint64)
    for i,p in enumerate(data):
        for q in list(data)[i+1:]:
            hs1=set(hashes[p].tolist());hs2=set(hashes[q].tolist());common=hs1&hs2
            pairs.append({'proyecto_a':p,'proyecto_b':q,'vectores_identicos':len(common),
               'filas_de_a_coincidentes':int(np.isin(hashes[p],list(common)).sum()),
               'filas_de_b_coincidentes':int(np.isin(hashes[q],list(common)).sum())})
    return pd.DataFrame(pairs)


def pack(data,projects):
    """Cada ejemplo pertenece a su proyecto; sin derivar información de ningún test."""
    return (pd.concat([data[p][0] for p in projects],ignore_index=True),
            pd.concat([data[p][1] for p in projects],ignore_index=True))


def make_pipeline(scenario_id,algorithm):
    _,balance,select=next(v for v in SCENARIOS if v[0]==scenario_id)
    # Selectores y balanceadores DENTRO del pipeline: se ajustan solo en training.
    if select=='MI':
        selector=SelectKBest(partial(mutual_info_classif,random_state=SEED), k=10)
    elif select=='RF':
        selector=SelectFromModel(RandomForestClassifier(n_estimators=100,random_state=SEED,n_jobs=1),threshold='median')
    else: selector='passthrough'
    if balance=='SMOTE': sampler=SMOTE(random_state=SEED,k_neighbors=3)
    elif balance=='ADASYN':sampler=ADASYN(random_state=SEED,n_neighbors=3)
    else:sampler='passthrough'
    if algorithm=='SVM':
        model=SVC(C=1.0,kernel='rbf',gamma='scale',probability=False,random_state=SEED,cache_size=512)
    elif algorithm=='Random Forest':
        model=RandomForestClassifier(n_estimators=200,max_depth=12,random_state=SEED,n_jobs=1)
    elif algorithm=='XGBoost':
        model=XGBClassifier(n_estimators=160,max_depth=3,learning_rate=0.1,
          objective='binary:logistic',eval_metric='logloss',tree_method='hist',
          random_state=SEED,n_jobs=1)
    else: raise ValueError(algorithm)
    return Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),
        ('scaler',StandardScaler()),('selection',selector),('sampler',sampler),('model',model)])


def raw_score(pipe,X):
    if hasattr(pipe,'predict_proba'):
        classes=list(pipe.classes_)
        return np.asarray(pipe.predict_proba(X)[:,classes.index(1)],dtype=float),'probabilidad_no_calibrada'
    if hasattr(pipe,'decision_function'):
        return np.asarray(pipe.decision_function(X),dtype=float),'margen_no_calibrado'
    raise ValueError('No hay score utilizable')


def metrics(pipe,X,y):
    y=np.asarray(y,dtype=int)
    yp=np.asarray(pipe.predict(X),dtype=int)
    s,kind=raw_score(pipe,X)
    if not np.isfinite(s).all(): raise ValueError('Score no finito')
    cm=confusion_matrix(y,yp,labels=[0,1])
    result={'n':len(y),'positivos':int(y.sum()),'prevalencia':float(y.mean()),
       'f1':float(f1_score(y,yp,zero_division=0)),
       'average_precision':float(average_precision_score(y,s)),
       'auc_roc':float(roc_auc_score(y,s)) if len(np.unique(y))==2 else None,
       'precision':float(precision_score(y,yp,zero_division=0)),
       'recall':float(recall_score(y,yp,zero_division=0)),
       'accuracy':float(accuracy_score(y,yp)),
       'tn':int(cm[0,0]),'fp':int(cm[0,1]),'fn':int(cm[1,0]),'tp':int(cm[1,1]),
       'score_tipo':kind}
    return result,s,yp


def ranking_metrics(y,score,loc,fracs=(.1,.2,.3)):
    y=np.asarray(y,dtype=int);n=len(y);pos=int(y.sum())
    if pos==0: return []
    idx=np.arange(n)
    out=[]
    ranks={'ML':np.lexsort((idx,-score)),'LOC':np.lexsort((idx,-np.asarray(loc,dtype=float)))}
    for f in fracs:
        k=max(1,int(np.ceil(n*f)))
        for name,order in ranks.items():
            true=int(y[order[:k]].sum())
            out.append({'metodo':name,'fraccion':f,'k':k,'detectados':true,
               'precision_at_k':true/k,'recall_at_k':true/pos,
               'lift_at_k':(true/k)/float(y.mean())})
        out.append({'metodo':'Aleatorio_esperado','fraccion':f,'k':k,'detectados':None,
            'precision_at_k':float(y.mean()),'recall_at_k':k/n,'lift_at_k':1.0})
    return out



def deduplicar_global(data, seed=SEED):
    """Desduplicación PREVIA a los folds, basada SOLO en vectores X.

    Una huella idéntica en cualquier proyecto puede pertenecer a un solo registro
    del conjunto científico. Se elige de manera determinista un registro mediante
    sha256(huella, proyecto), sin usar las etiquetas ni los resultados de test.
    Todas las eliminaciones se registran. Conservar un único registro no demuestra
    independencia de los proyectos; se considera una sensibilidad metodológica.
    """
    grupos = {}
    for p,(X,y) in data.items():
        for i,h in enumerate(pd.util.hash_pandas_object(X[list(FEATURES)],index=False).to_numpy(dtype=np.uint64)):
            grupos.setdefault(int(h),[]).append((p,i,int(y.iloc[i])))
    conservados={p:set() for p in data}
    con_conflicto=0; filas_con_conflicto=0; cross_groups=0; grupos_repetidos=0
    detalle=[]
    for h,filas in grupos.items():
        if len(filas)>1:
            grupos_repetidos+=1
            if len({p for p,_,_ in filas})>1: cross_groups+=1
            if len({y for _,_,y in filas})>1:
                con_conflicto+=1;filas_con_conflicto+=len(filas)
        # Elección no basada en y ni en orden de proyectos; desempate por posición.
        elegido=min(filas,key=lambda r:(hashlib.sha256(f'{seed}|{h}|{r[0]}'.encode()).hexdigest(),r[1]))
        conservados[elegido[0]].add(elegido[1])
    salida={}; reporte=[]
    for p,(X,y) in data.items():
        indices=sorted(conservados[p])
        X2=X.iloc[indices].reset_index(drop=True)
        y2=y.iloc[indices].reset_index(drop=True)
        if len(X2)<20 or y2.nunique()!=2:
            raise ValueError(f'La deduplicación deja {p} sin muestra/clases adecuadas: n={len(X2)}, clases={y2.value_counts().to_dict()}')
        salida[p]=(X2,y2)
        reporte.append({'proyecto':p,'filas_originales':len(X), 'filas_deduplicadas':len(X2),
          'filas_eliminadas':len(X)-len(X2),'positivos_originales':int(y.sum()),
          'positivos_deduplicados':int(y2.sum()),'prevalencia_deduplicada':float(y2.mean())})
    huellas=[]
    for X,_ in salida.values():
        huellas.extend(pd.util.hash_pandas_object(X[list(FEATURES)],index=False).to_numpy(dtype=np.uint64).tolist())
    assert len(huellas)==len(set(huellas)), 'Error: todavía hay huellas X repetidas'
    resumen={'metodo':'Una ocurrencia por huella de las 21 métricas a escala global ANTES de las particiones; propietario determinado sin y',
       'huellas_unicas':len(grupos),'grupos_repetidos':grupos_repetidos,
       'grupos_repetidos_entre_proyectos':cross_groups,
       'grupos_con_etiquetas_contradictorias':con_conflicto,
       'filas_afectadas_por_etiquetas_contradictorias':filas_con_conflicto,
       'eliminados_totales':sum(len(X) for X,_ in data.values())-sum(len(X) for X,_ in salida.values()),
       'nota':'Los valores de etiqueta contradictorios se auditan, pero NO se usan para decidir qué instancia se conserva; la selección basada en y ocasionaría fuga.'}
    return salida,pd.DataFrame(reporte),resumen


def curva_esfuerzo(y, cost, order):
    """Curva de recall vs proporción de LOC. Área/interpolación lineal por módulo;
    esto NO equivale a inspeccionar literalmente una fracción de un módulo.
    """
    y=np.asarray(y,dtype=int)[order]
    c=np.asarray(cost,dtype=float)[order]
    xs=np.r_[0,np.cumsum(c)/c.sum()]
    ys=np.r_[0,np.cumsum(y)/y.sum()]
    return xs,ys


def area_hasta(xs,ys,fin=.2):
    if fin<=0 or fin>1:raise ValueError(fin)
    mask=(xs<fin)
    x=np.r_[xs[mask],fin]
    y=np.r_[ys[mask],np.interp(fin,xs,ys)]
    return float(np.trapz(y,x) if not hasattr(np,'trapezoid') else np.trapezoid(y,x))


def esfuerzo_qa(y, score, loc, proyecto, contexto, fracciones=(.1,.2,.3)):
    """Popt@20% LOC y Recall@%LOC, sobre MODULOS positivos (no total de bugs).
    Ranking LOC-desc = regla sencilla. OPT/WORST usan y solo como techo de referencia
    para Popt, JAMÁS para entrenar o desplegar el modelo.
    """
    y=np.asarray(y,dtype=int)
    s=np.asarray(score,dtype=float)
    costs=np.asarray(loc,dtype=float)
    if len(y)==0 or y.sum()==0 or len(y)!=len(s) or len(y)!=len(costs):
        raise ValueError('La evaluación de esfuerzo requiere módulos etiquetados positivos y tamaños correspondientes')
    if not np.isfinite(costs).all() or (costs<0).any() or not np.isfinite(s).all():
        raise ValueError('LOC/score deben ser finitos; LOC no puede ser negativo. Revisar origen.')
    # Cada módulo debe costar como mínimo 1 LOC para que la curva sea estrictamente creciente.
    costs=np.maximum(costs,1.0)
    ids=np.arange(len(y))
    ordenes={
      'ML':np.lexsort((ids,-s)),
      'LOC_desc':np.lexsort((ids,-costs)),
      'OPT_teorico':np.lexsort((ids,-y/costs)),
      'WORST_teorico':np.lexsort((ids,y/costs))}
    curvas={name:curva_esfuerzo(y,costs,ord_) for name,ord_ in ordenes.items()}
    area_opt=area_hasta(*curvas['OPT_teorico'])
    area_worst=area_hasta(*curvas['WORST_teorico'])
    den=area_opt-area_worst
    registros=[]
    for name,order in ordenes.items():
        x,r=curvas[name]; area=area_hasta(x,r)
        valores={}
        for f in fracciones:
            # interpolación para la curva integrada; estimación explícitamente ilustrativa de fracción de módulo
            valores[f'recall_interp_{int(f*100)}pct_loc']=float(np.interp(f,x,r))
            # módulos inspeccionados COMPLETAMENTE sin exceder el % LOC: valor conservador y operativo
            num=int(np.searchsorted(x,f,side='right')-1)
            valores[f'recall_modulos_completos_{int(f*100)}pct_loc']=float(y[order[:num]].sum()/y.sum())
        registros.append({'proyecto_test':proyecto,'contexto':contexto,'metodo':name,
          'positivos_totales':int(y.sum()),'modulos':len(y),'loc_total_proxy':float(costs.sum()),
          'area_0_20':area,'popt_20':float((area-area_worst)/den) if den>1e-12 else None,
          **valores})
    return registros


def firma_datos(data):
    h=hashlib.sha256()
    for name in sorted(data):
        X,y=data[name]
        h.update(name.encode())
        h.update(pd.util.hash_pandas_object(X,index=False).to_numpy(dtype=np.uint64).tobytes())
        h.update(np.asarray(y,dtype=np.int8).tobytes())
    return h.hexdigest()


def evaluar_config_fija(data, scenario, algorithm, modo, contexto):
    """LOPO con configuración FIJA, sin selección interna. No es test nuevo del joblib.
    Tras seleccionar una receta con estos proyectos es un análisis descriptivo, NO prueba inédita.
    """
    rows=[]; qa=[]
    for target in data:
        fuentes=[p for p in data if p!=target]
        Xtr,ytr=pack(data,fuentes)
        Xte,yte=data[target]
        pipe=make_pipeline(scenario,algorithm)
        pipe.fit(Xtr,ytr)
        m,score,_=metrics(pipe,Xte,yte)
        rows.append({'modo':modo,'configuracion':contexto,'algoritmo':algorithm,
          'escenario':scenario,'proyecto_test':target,**m})
        qa.extend(esfuerzo_qa(yte,score,Xte['loc'].to_numpy(),target,contexto))
    return rows,qa


def config_hash(audits,projects,data,modo):
    info={'version':EXPERIMENT_VERSION,'datasets':{a['proyecto']:a['sha256'] for a in audits},
       'proyectos':list(projects),'candidatos':list(CANDIDATES),'seed':SEED,
       'modo':modo,'huella_datos_procesados':firma_datos(data),
       'librerias':{lib:version(lib) for lib in ['scikit-learn','imbalanced-learn','xgboost']}}
    return hashlib.sha256(json.dumps(info,sort_keys=True).encode()).hexdigest(),info


def eval_one_candidate(data,train_projects,scenario,algorithm):
    """Validación interna LOGO en PROYECTOS fuente; sin observar proyecto objetivo."""
    folds=[];tic=time.time()
    for validation_project in train_projects:
        fit_projects=[p for p in train_projects if p!=validation_project]
        X_tr,y_tr=pack(data,fit_projects)
        X_val,y_val=data[validation_project]
        pipe=make_pipeline(scenario,algorithm)
        pipe.fit(X_tr,y_tr)
        mm,_,_=metrics(pipe,X_val,y_val)
        folds.append({'proyecto_validacion':validation_project,
            **{k:mm[k] for k in ['n','positivos','f1','average_precision','auc_roc','precision','recall']}})
    return {'escenario':scenario,'algoritmo':algorithm,'n_folds':len(folds),
      'f1_macro':float(np.mean([d['f1'] for d in folds])),
      'ap_macro':float(np.mean([d['average_precision'] for d in folds])),
      'auc_macro':float(np.mean([d['auc_roc'] for d in folds])),
      'segundos':round(time.time()-tic,2),'error':None,'folds':folds}


def select_candidate(rows,expected_folds):
    good=[r for r in rows if r.get('error') is None and r.get('n_folds')==expected_folds]
    if not good:raise RuntimeError('Ningún candidato completo y válido')
    # Criterios fijados antes de ver proyectos reservados: F1 -> AP -> AUC.
    return sorted(good,key=lambda r:(-r['f1_macro'],-r['ap_macro'],-r['auc_macro'],
                                     r['escenario'],r['algoritmo']))[0]


def inner_search(data,projects,checkpoint,lock,*,candidate_limit=None):
    """Checkpoints por candidato (4 o 5 ajustes). Los errores se registran."""
    checkpoint=Path(checkpoint)
    if checkpoint.exists():
        saved=json.loads(checkpoint.read_text(encoding='utf-8'))
        if saved['config_hash']!=lock or saved['proyectos']!=list(projects):
            raise RuntimeError(f'Checkpoint incompatible: {checkpoint}; no se mezclan experimentos')
        rows=saved['rows']
    else: rows=[]
    done={(r['escenario'],r['algoritmo']) for r in rows}
    candidates=CANDIDATES[:candidate_limit] if candidate_limit else CANDIDATES
    for count,(scenario,algorithm) in enumerate(candidates,1):
        if (scenario,algorithm) in done:continue
        print(f'  candidato {count:02}/{len(candidates)} · {algorithm} / {scenario}',flush=True)
        try:
            row=eval_one_candidate(data,projects,scenario,algorithm)
            print(f"      F1(macro)={row['f1_macro']:.3f} · AP={row['ap_macro']:.3f}",flush=True)
        except Exception as exc:
            row={'escenario':scenario,'algoritmo':algorithm,'n_folds':0,
                 'f1_macro':None,'ap_macro':None,'auc_macro':None,
                 'segundos':None,'error':f'{type(exc).__name__}: {str(exc)[:400]}','folds':[]}
            print('      ERROR:',row['error'],flush=True)
        rows.append(row)
        jdump(checkpoint,{'config_hash':lock,'proyectos':list(projects),'rows':rows})
    return rows


def outer_test(data,target,selection,modo):
    sources=[p for p in data if p!=target]
    Xt,yt=pack(data,sources)
    Xo,yo=data[target]
    pipe=make_pipeline(selection['escenario'],selection['algoritmo'])
    pipe.fit(Xt,yt)
    m,score,pred=metrics(pipe,Xo,yo)
    src_hash=set(pd.util.hash_pandas_object(Xt,index=False).to_numpy(dtype=np.uint64).tolist())
    tgt_hash=pd.util.hash_pandas_object(Xo,index=False).to_numpy(dtype=np.uint64)
    unseen=np.asarray([int(h) not in src_hash for h in tgt_hash],dtype=bool)
    m.update({'proyecto_test':target,'proyectos_entrenamiento':sources,
       'escenario':selection['escenario'],'algoritmo':selection['algoritmo'],
       'cv_f1_macro_fuente':selection['f1_macro'],
       'vectores_test_presentes_en_train':int((~unseen).sum()),
       'modo':modo,'validation_protocolo':'nested_leave_one_project_out'})
    ranks=ranking_metrics(yo,score,Xo['loc'].to_numpy())
    for r in ranks:
        r['proyecto_test']=target
        r['modo']=modo
    qa=esfuerzo_qa(yo,score,Xo['loc'].to_numpy(),target,'seleccion_anidada')
    return m,ranks,qa


def run_nested(data,audits,results,*,modo,candidate_limit=None):
    """Evaluación anidada de la REGLA de selección, independiente del modelo final.
    Luego selecciona una configuración mediante LOPO global (cinco proyectos) y
    exporta exactamente UN pipeline entrenado en las fuentes de ese modo.
    """
    results=Path(results);results.mkdir(parents=True,exist_ok=True)
    names=list(data)
    lock,config=config_hash(audits,names,data,modo)
    jdump(results/'configuracion.json',{'hash':lock,'especificacion':config,
      'advertencias':['Procedencia documental no acreditada','LOC aproximación a esfuerzo real',
        'F1 de procedimiento outer NO es una prueba independiente del .joblib final',
        'Popt@20 es área normalizada con interpolación por módulo; reportar junto a resultados de módulos completos']})
    outer=[];rank=[];effort=[];por_algoritmo=[]
    for i,target in enumerate(names,1):
        print(f'\n[{modo}] TEST EXTERNO {i}/{len(names)}: {target}',flush=True)
        source=[p for p in names if p!=target]
        rows=inner_search(data,source,results/f'inner_{target}.json',lock,candidate_limit=candidate_limit)
        chosen=select_candidate(rows,len(source))
        print(f"   Configuración elegida internamente: {chosen['algoritmo']} / {chosen['escenario']}",flush=True)
        for algoritmo in ALGORITHMS:
            candidates_algo=[r for r in rows if r['algoritmo']==algoritmo and r.get('error') is None]
            if not candidates_algo: continue
            elegido_algo=select_candidate(candidates_algo,len(source))
            m,r,e=outer_test(data,target,elegido_algo,modo)
            m['elegido_procedimiento_general']=bool(algoritmo==chosen['algoritmo'])
            por_algoritmo.append(m)
            if algoritmo==chosen['algoritmo']:
                outer.append(m);rank.extend(r);effort.extend(e)
                jdump(results/f'test_externo_{target}.json',m)
            print(f"   {algoritmo}: F1={m['f1']:.3f} | AP={m['average_precision']:.3f}",flush=True)
        pd.DataFrame([{k:v for k,v in r.items() if k!='folds'} for r in rows]).to_csv(
            results/f'candidatos_inner_{target}.csv',index=False)
        pd.DataFrame(outer).to_csv(results/'resultados_por_proyecto.csv',index=False)
        pd.DataFrame(effort).to_csv(results/'qa_esfuerzo_nested.csv',index=False)
    assert len(outer)==len(names),'No todos los folds externos terminaron correctamente'
    pd.DataFrame(por_algoritmo).to_csv(results/'comparacion_algoritmos_outer.csv',index=False)
    comp=pd.DataFrame(por_algoritmo).groupby('algoritmo',as_index=False).agg(
        f1_macro_externo=('f1','mean'),ap_macro_externo=('average_precision','mean'),
        auc_macro_externo=('auc_roc','mean'),recall_macro_externo=('recall','mean'),
        proyectos_evaluados=('proyecto_test','nunique'))
    comp.sort_values(['f1_macro_externo','ap_macro_externo'],ascending=False).to_csv(
        results/'resumen_algoritmos_externos.csv',index=False)
    pd.DataFrame(rank).to_csv(results/'qa_recall_por_modulos.csv',index=False)
    jdump(results/'resultados_outer.json',outer)
    print(f'\n[{modo}] SELECCION GLOBAL mediante cinco folds LOGO',flush=True)
    rows=inner_search(data,names,results/'seleccion_final_cv.json',lock,candidate_limit=candidate_limit)
    winning=select_candidate(rows,len(names))
    pd.DataFrame([{k:v for k,v in row.items() if k!='folds'} for row in rows]).to_csv(
        results/'comparacion_global_cpdp.csv',index=False)
    X_all,y_all=pack(data,names)
    pipe=make_pipeline(winning['escenario'],winning['algoritmo'])
    pipe.fit(X_all,y_all)
    manifest={'protocolo':EXPERIMENT_VERSION,'nombre':'Modelo_general_CPDP',
        'algoritmo':winning['algoritmo'],'escenario':winning['escenario'],
        'seleccion_criterios':'F1 positivo promedio por proyecto; desempate AP y AUC en LOGO',
        'cv_global_f1':winning['f1_macro'],'cv_global_ap':winning['ap_macro'],
        'cv_global_auc':winning['auc_macro'],'datasets_entrenamiento':names,
        'columnas':list(FEATURES),'etiqueta':'1=defecto_historico_registrado',
        'modo_preprocesamiento':modo,'huella_datos_entrenados':firma_datos(data),
        'datos_entrenamiento_cantidad':len(y_all),'documentally_verified':False,
        'score_aviso':'SVM=margin no calibrado / RF y XGB=salida no calibrada',
        'fuentes':{a['proyecto']:a['sha256'] for a in audits},
        'seleccion_global_reentrenada_con_5_proyectos':True,
        'limite':'Sin sexto proyecto externo, F1 global no es prueba independiente del archivo joblib final.',
        'creado_utc':datetime.now(timezone.utc).isoformat()}
    bundle={'pipeline':pipe,'manifest':manifest,'columnas':list(FEATURES)}
    joblib.dump(bundle,results/'modelo_general_cpdp.joblib',compress=3)
    jdump(results/'manifiesto_modelo_general.json',manifest)
    pd.DataFrame(columns=['id_modulo',*FEATURES]).to_csv(results/'plantilla_para_streamlit.csv',index=False)
    # Este contraste de recetas fijas se declara exploratorio cuando ya se escogió con estos mismos proyectos.
    comparacion_fija=[];comparacion_esfuerzo=[]
    for sid,algo,nombre in [('E0_BASELINE','SVM','SVM_base'),
                            ('E7_SMOTE_RF','SVM','SVM_SMOTE_RF')]:
        print(f'[{modo}] Comparación intra-SVM: {nombre}',flush=True)
        rr,qq=evaluar_config_fija(data,sid,algo,modo,nombre)
        comparacion_fija.extend(rr);comparacion_esfuerzo.extend(qq)
    pd.DataFrame(comparacion_fija).to_csv(results/'comparacion_SVM_base_vs_SVM_E7.csv',index=False)
    pd.DataFrame(comparacion_esfuerzo).to_csv(results/'qa_esfuerzo_comparacion_SVM.csv',index=False)
    # Verificaciones reproducibles de congruencia del artefacto.
    loaded=joblib.load(results/'modelo_general_cpdp.joblib')
    assert loaded['manifest']['algoritmo']==winning['algoritmo']
    assert loaded['manifest']['escenario']==winning['escenario']
    assert list(loaded['columnas'])==list(FEATURES)
    assert len(loaded['pipeline'].predict(X_all.head(3)))==3
    summary={'modo':modo,'candidatos_por_busqueda':len(CANDIDATES) if candidate_limit is None else candidate_limit,
       'folds_externos':len(names),'macro_f1_outer':float(np.mean([r['f1'] for r in outer])),
       'macro_ap_outer':float(np.mean([r['average_precision'] for r in outer])),
       'macro_auc_outer':float(np.mean([r['auc_roc'] for r in outer])),
       'ganador_final':{'algoritmo':winning['algoritmo'],'escenario':winning['escenario'],
         'f1_cv_proyectos':winning['f1_macro'],'ap_cv_proyectos':winning['ap_macro']},
       'nota':'Nested outer estima procedimiento selección por proyecto; final es receta global reentrenada. Sin prueba inédita del joblib.'}
    jdump(results/'resumen_final.json',summary)
    return summary


def inference(bundle,df):
    """Solo para prueba de integración; interfaz productiva será Streamlit."""
    if 'id_modulo' in df.columns:
        ids=df['id_modulo'].astype(str).tolist()
    else:ids=[f'modulo_{i+1:04}' for i in range(len(df))]
    X,aliases=harmonize_features(df.drop(columns=['id_modulo'],errors='ignore'), 'CSV externo',allow_extra=False)
    pipe=bundle['pipeline']
    score,kind=raw_score(pipe,X)
    yp=pipe.predict(X)
    out=pd.DataFrame({'id_modulo':ids,'clase_predicha':yp.astype(int),
        'score_riesgo':score,'tipo_score':kind})
    return out.sort_values('score_riesgo',ascending=False,kind='stable').reset_index(drop=True).assign(
        prioridad=lambda x:np.arange(1,len(x)+1))


def descargar_datos_nuevos(raw_dir, timeout=75):
    """Siempre descarga fuentes públicas; no lee carpetas ni resultados de versiones anteriores."""
    import urllib.request
    raw_dir=Path(raw_dir);raw_dir.mkdir(parents=True,exist_ok=True)
    registros=[]
    for p in PROJECTS:
        url=f'{SOURCE_BASE}/{p.lower()}.csv'
        destino=raw_dir/f'{p}.csv'
        if destino.exists():
            raise FileExistsError(f'Para asegurar el inicio desde cero, la ruta ya existe: {destino}')
        request=urllib.request.Request(url,headers={'User-Agent':'tesis-cpdp-reproducible/1.0'})
        with urllib.request.urlopen(request,timeout=timeout) as response:
            blob=response.read(25_000_001)
        if not (1000<len(blob)<=25_000_000):
            raise RuntimeError(f'{p}: tamaño de descarga sospechoso ({len(blob)})')
        destino.write_bytes(blob)
        try:
            _,_,aud=load_project(destino,p)
        except Exception:
            destino.unlink(missing_ok=True)
            raise
        registros.append({'proyecto':p,'url':url,'archivo':destino.name,'sha256':aud['sha256'],
                          'registros':aud['filas'],'variable_objetivo':aud['etiqueta_original']})
        print(f'{p}: {aud["filas"]} registros; SHA-256={aud["sha256"][:12]}...')
    return pd.DataFrame(registros)
