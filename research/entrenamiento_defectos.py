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
EXPERIMENT_ID = 'CPDP_NESTED_LOPO_DEDUP_ESFUERZO'
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
    del conjunto científico. Se conserva de forma determinista un registro mediante
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
    info={'identificador_experimento':EXPERIMENT_ID,'datasets':{a['proyecto']:a['sha256'] for a in audits},
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
    manifest={'protocolo':EXPERIMENT_ID,'nombre':'Modelo_general_CPDP',
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
    """Siempre descarga fuentes públicas; utiliza únicamente archivos descargados en el directorio nuevo de entrada."""
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




# Evaluación de priorización y sensibilidad para la investigación.
from scipy.stats import wilcoxon

METODOS = ('ML', 'ManualUp', 'LOC_desc', 'Aleatorio_esperado')
PRESUPUESTOS = (0.10, 0.20, 0.30)

def json_save(dest, obj):
    jdump(dest, obj)

def project_keys(data):
    """Huella de las 21 características; no incluye etiqueta ni origen."""
    return {p: pd.util.hash_pandas_object(X.loc[:, list(FEATURES)],index=False).to_numpy(dtype=np.uint64)
            for p,(X,_) in data.items()}

def contradiction_audit(data, out_dir):
    """Busca X idénticas con etiquetas discordantes ANTES de particionar.

    La eliminación de grupos basada en y es un análisis de sensibilidad de un
    benchmark histórico completamente etiquetado; no es filtrado aplicable a
    proyectos nuevos sin etiquetas y no se presenta como prueba ciega.
    """
    keys=project_keys(data)
    group={}
    for project,(X,y) in data.items():
        for ix,(h,lab) in enumerate(zip(keys[project],np.asarray(y,dtype=int))):
            group.setdefault(int(h),[]).append((project,int(ix),int(lab)))
    ambiguous={k for k,rows in group.items() if len(set(v[2] for v in rows))>1}
    details=[]
    for h in sorted(ambiguous):
        vals=group[h]
        details.append({'huella_vector_u64':str(h),'filas':len(vals),
                        'proyectos':','.join(sorted(set(v[0] for v in vals))),
                        'conteo_clase_0':sum(v[2]==0 for v in vals),
                        'conteo_clase_1':sum(v[2]==1 for v in vals),
                        'filas_referenciadas':';'.join(f'{p}:{i}' for p,i,_ in vals)})
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(details).to_csv(out_dir/'grupos_etiquetas_contradictorias.csv',index=False)
    data_filtered={};report=[]
    for p,(X,y) in data.items():
        keep=~np.isin(keys[p],np.array(list(ambiguous),dtype=np.uint64))
        x=X.iloc[np.flatnonzero(keep)].reset_index(drop=True)
        yy=y.iloc[np.flatnonzero(keep)].reset_index(drop=True)
        if len(x)<20 or yy.nunique()!=2:
            raise ValueError(f'{p}: política DESCARTAR_CONFLICTOS no mantiene ambas clases')
        data_filtered[p]=(x,yy)
        report.append({'proyecto':p,'filas_antes':len(y),
                       'filas_eliminadas_por_conflicto':int((~keep).sum()),
                       'filas_despues':len(yy),'positivos_despues':int(yy.sum())})
    pd.DataFrame(report).to_csv(out_dir/'impacto_conflictos_por_proyecto.csv',index=False)
    return data_filtered,{'grupos_contradictorios':len(ambiguous),
                          'filas_en_grupos_contradictorios':sum(len(group[k]) for k in ambiguous),
                          'regla_principal':'Conservar una sola X global, propietario elegido sin consultar la etiqueta.',
                          'regla_sensibilidad':'Descartar los grupos contradictorios del corpus etiquetado y después conservar una sola X por grupo.',
                          'advertencia':'El descarte usa etiquetas del corpus entero como limpieza de benchmark; NO puede simularse en un nuevo proyecto sin y. Resultados solo análisis de sensibilidad.'}

def preparar_cohortes(original,out_dir):
    out_dir=Path(out_dir)
    primary, r_primary, s_primary=deduplicar_global(original)
    reduced,s_conf=contradiction_audit(original,out_dir/'auditoria')
    sensitivity,r_sens,s_sens=deduplicar_global(reduced)
    for name,data in [('deduplicado',primary),('sin_grupos_conflictivos',sensitivity)]:
        audit=overlap_audit(data)
        if audit['vectores_identicos'].sum()!=0:
            raise AssertionError(f'{name} todavía tiene solapamiento')
        audit.to_csv(out_dir/'auditoria'/f'solapamiento_{name}.csv',index=False)
    r_primary.to_csv(out_dir/'auditoria'/'dedup_principal_por_proyecto.csv',index=False)
    r_sens.to_csv(out_dir/'auditoria'/'dedup_sensibilidad_por_proyecto.csv',index=False)
    report={'original_total':sum(len(y) for _,y in original.values()),
            'principal_total':sum(len(y) for _,y in primary.values()),
            'sensibilidad_total':sum(len(y) for _,y in sensitivity.values()),
            'principal_resumen':s_primary,'sensibilidad_resumen':s_sens,
            'conflictos':s_conf,
            'huella_principal':firma_datos(primary),
            'huella_sensibilidad':firma_datos(sensitivity)}
    json_save(out_dir/'auditoria'/'resumen_cohortes.json',report)
    return {'sin_deduplicar':original,'deduplicado':primary,
            'sin_grupos_conflictivos':sensitivity},report

def safe_areas(y,c,orders, fraction):
    """Popt normalizado: (A_metodo-A_worst)/(A_opt-A_worst).
    A hasta fracción de LOC con interpolación LINEAL para curva, no inspección
    real de una fracción de módulo; además se reporta recall de módulos completos.
    """
    lines={key:curva_esfuerzo(y,c,order) for key,order in orders.items()}
    a_opt=area_hasta(*lines['OPT_teorico'],fin=fraction)
    a_worst=area_hasta(*lines['WORST_teorico'],fin=fraction)
    return lines, a_opt, a_worst

def ranking_evaluation(y, s, loc, *, project, cohort, procedimiento, random_repeats=50):
    y=np.asarray(y,dtype=int);s=np.asarray(s,dtype=float);loc=np.asarray(loc,dtype=float)
    if len(y)!=len(s) or len(y)!=len(loc) or not np.isfinite(s).all():
        raise ValueError('Score o tamaños incompatibles')
    if not np.isfinite(loc).all() or (loc < 0).any():
        raise ValueError('LOC no finito o negativo; no es esfuerzo válido')
    if int(y.sum())==0 or len(np.unique(y))!=2:
        raise ValueError('Proyecto test sin ambas clases')
    if random_repeats<1: raise ValueError('random_repeats debe ser positivo')
    loc_cost=np.maximum(loc,1.0)
    n=len(y); idx=np.arange(n);positive=int(y.sum())
    orders={
       'ML':np.lexsort((idx,-s)),
       'ManualUp':np.lexsort((idx,loc_cost)),
       'LOC_desc':np.lexsort((idx,-loc_cost)),
       'OPT_teorico':np.lexsort((idx,-y/loc_cost)),
       'WORST_teorico':np.lexsort((idx,y/loc_cost)),
    }
    # La definición de aleatorio como media de permutaciones, no un ranking elegido por etiquetas.
    rng=np.random.default_rng(SEED+sum(map(ord,project))+len(cohort))
    random_orders=[rng.permutation(n) for _ in range(random_repeats)]
    output=[]
    for method in METODOS:
        these_orders=random_orders if method=='Aleatorio_esperado' else [orders[method]]
        for f in PRESUPUESTOS:
            k=max(1,int(np.ceil(n*f)))
            module_recalls=[float(y[order[:k]].sum()/positive) for order in these_orders]
            # Para LOC no se sobrepasa el presupuesto: solo módulos completos.
            budget=f*float(loc_cost.sum())
            values=[]; reals=[]; areas=[]; areas_full=[]
            for order in these_orders:
                xs,ys=curva_esfuerzo(y,loc_cost,order)
                cost_used=np.cumsum(loc_cost[order])
                complete=int(np.searchsorted(cost_used,budget,side='right'))
                values.append(float(y[order[:complete]].sum()/positive))
                reals.append(float(np.interp(f,xs,ys)))
                areas.append(area_hasta(xs,ys,fin=.2))
                areas_full.append(area_hasta(xs,ys,fin=1.0))
            _,opt20,worst20=safe_areas(y,loc_cost,orders,.2)
            _,optfull,worstfull=safe_areas(y,loc_cost,orders,1.0)
            area20=float(np.mean(areas));area_full=float(np.mean(areas_full))
            p20=(area20-worst20)/(opt20-worst20) if opt20-worst20>1e-12 else np.nan
            pfull=(area_full-worstfull)/(optfull-worstfull) if optfull-worstfull>1e-12 else np.nan
            output.append({'cohorte':cohort,'procedimiento':procedimiento,'proyecto':project,
                           'metodo':method,'presupuesto_fraccion':f,
                           'n_modulos':n,'n_positivos':positive,'k_modulos':k,
                           'recall_por_modulos':float(np.mean(module_recalls)),
                           'recall_por_LOC_modulos_completos':float(np.mean(values)),
                           'recall_por_LOC_interpolado':float(np.mean(reals)),
                           'popt_normalizado_0_20':float(p20),
                           'popt_normalizado_0_100':float(pfull),
                           'A20_metodo':area20,'A20_optimo':opt20,'A20_peor':worst20,
                           'A100_metodo':area_full,'A100_optimo':optfull,'A100_peor':worstfull,
                           'loc_total_proxy':float(loc_cost.sum()),
                           'aleatorio_n_permutaciones':random_repeats if method=='Aleatorio_esperado' else 0})
    return output

def evaluate_fixed_configs(data,cohort,result_dir, configs=('E6_ADASYN_MI','E7_SMOTE_RF')):
    result_dir=Path(result_dir);result_dir.mkdir(parents=True,exist_ok=True)
    rows=[]; rank=[]
    for target in PROJECTS:
        src=[p for p in PROJECTS if p!=target]
        Xt,yt=pack(data,src)
        Xo,yo=data[target]
        for scenario in configs:
            print(f'[ {cohort}] prueba LOPO fija · {target} · {scenario}',flush=True)
            pipe=make_pipeline(scenario,'SVM')
            start=time.perf_counter()
            pipe.fit(Xt,yt)
            t_fit=time.perf_counter()-start
            start=time.perf_counter()
            m,score,pred=metrics(pipe,Xo,yo)
            t_test=time.perf_counter()-start
            rows.append({'cohorte':cohort,'proyecto':target,'algoritmo':'SVM',
                         'escenario':scenario,'segundos_entrenamiento':t_fit,
                         'segundos_inferencia_evaluacion':t_test,**m})
            rank.extend(ranking_evaluation(yo,score,Xo['loc'],project=target,
                          cohort=cohort,procedimiento=f'SVM_{scenario}'))
    rr=pd.DataFrame(rows);qq=pd.DataFrame(rank)
    rr.to_csv(result_dir/'E6_vs_E7_por_proyecto.csv',index=False)
    qq.to_csv(result_dir/'E6_vs_E7_ranking_por_proyecto.csv',index=False)
    return rr,qq

def paired_tests(df, cohort, output_dir):
    """Comparación E6/E7 apareada por proyecto; p descriptivos, no confirmatorios.
    Con 5 diferencias sin empates, el menor p exacto bilateral de Wilcoxon es 0.0625.
    """
    subset=df[df['cohorte']==cohort]
    records=[]
    p_values=[]
    for key in ['f1','average_precision','auc_roc','recall']:
        pivot=subset.pivot(index='proyecto',columns='escenario',values=key)
        a=pivot['E6_ADASYN_MI'].to_numpy(dtype=float)
        b=pivot['E7_SMOTE_RF'].to_numpy(dtype=float)
        delta=a-b
        if not np.isfinite(delta).all(): raise ValueError(f'{key}: faltan métricas por proyecto')
        if np.allclose(delta,0):p_value=1.0;stat=0.0
        else:
            res=wilcoxon(delta,zero_method='wilcox',alternative='two-sided',method='exact')
            p_value=float(res.pvalue);stat=float(res.statistic)
        rng=np.random.default_rng(312)
        boots=np.mean(rng.choice(delta,size=(10000,len(delta)),replace=True),axis=1)
        rec={'cohorte':cohort,'metrica':key,'n_proyectos':len(delta),
             'media_E6':float(a.mean()),'media_E7':float(b.mean()),
             'media_diferencia_E6_menos_E7':float(delta.mean()),
             'mediana_diferencia':float(np.median(delta)),
             'desviacion_F1_E6_o_metrica':float(np.std(a,ddof=1)),
             'desviacion_F1_E7_o_metrica':float(np.std(b,ddof=1)),
             'proyectos_E6_mayor':int((delta>0).sum()),'proyectos_E7_mayor':int((delta<0).sum()),
             'wilcoxon_w':stat,'p_bilateral_exacto_exploratorio':p_value,
             'bootstrap_intervalo_95_descriptivo_inferior':float(np.quantile(boots,.025)),
             'bootstrap_intervalo_95_descriptivo_superior':float(np.quantile(boots,.975)),
             'precaucion':'Solo 5 proyectos; sin significancia no equivale a equivalencia; comparaciones en corpus usado para selección.'}
        records.append(rec)
    table=pd.DataFrame(records)
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    table.to_csv(output_dir/f'prueba_pareada_{cohort}.csv',index=False)
    return table

def summarize_rankings(tables,output_dir):
    rows=pd.concat(tables,ignore_index=True)
    rows.to_csv(Path(output_dir)/'QA_detalle_por_proyecto.csv',index=False)
    fields=['recall_por_modulos','recall_por_LOC_modulos_completos','recall_por_LOC_interpolado',
            'popt_normalizado_0_20','popt_normalizado_0_100']
    summary=(rows.groupby(['cohorte','procedimiento','metodo','presupuesto_fraccion'],as_index=False)
                 [fields].mean())
    summary.to_csv(Path(output_dir)/'QA_promedios_proyecto.csv',index=False)
    return summary

def quick_selfcheck():
    # Test de las funciones sin entrenar ningún modelo ni consultar fuentes.
    y=np.array([1,0,0,0,0,1,0,0,0,0],dtype=int)
    loc=np.array([1,50,60,70,80,2,90,100,110,120],dtype=float)
    score=np.array([9,0,1,2,3,8,4,5,6,7],dtype=float)
    x=ranking_evaluation(y,score,loc,project='PRUEBA',cohort='PRUEBA',procedimiento='PRUEBA',random_repeats=3)
    assert len(x)==len(METODOS)*len(PRESUPUESTOS)
    for r in x:
        assert 0<=r['recall_por_modulos']<=1
        assert 0<=r['recall_por_LOC_modulos_completos']<=1
        assert 0<=r['recall_por_LOC_interpolado']<=1
        if r['metodo']=='ManualUp' and r['presupuesto_fraccion']==.2:
            assert r['recall_por_LOC_modulos_completos']==1
    # Popt normalizado debe devolver 1 (óptimo) y 0 (peor), en curvas ideales.
    orders={'OPT_teorico':np.lexsort((np.arange(10),-y/loc)),
            'WORST_teorico':np.lexsort((np.arange(10),y/loc))}
    _,opt,worst=safe_areas(y,loc,orders,.2)
    assert opt>worst
    assert abs((opt-worst)/(opt-worst)-1)<1e-12
    print('Verificaciones de ranking y esfuerzo: OK (ranking, LOC, Popt y presupuestos).')
