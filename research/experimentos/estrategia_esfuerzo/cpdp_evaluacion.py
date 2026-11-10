"""T2 CPDP. Código integrado de auditoría y evaluación del experimento; no requiere otros notebooks.

No reemplazar el artefacto de Streamlit hasta revisión humana y pruebas de integración.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
import joblib
import cpdp_core as base

EXPERIMENTO_ID = 'CPDP_T2_QA_CALIBRACION_ESFUERZO'
METODOS = ('ML', 'ManualUp', 'LOC_desc', 'Aleatorio_esperado')
PRESUPUESTOS = (0.10, 0.20, 0.30)
SEED = 42


def json_save(dest, obj):
    base.jdump(dest, obj)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_keys(data):
    """Huella de las 21 características; no incluye etiqueta ni origen."""
    return {p: pd.util.hash_pandas_object(X.loc[:, list(base.FEATURES)],index=False).to_numpy(dtype=np.uint64)
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
                          'regla_principal':'Conservar una sola X global, propietario elegido sin consultar y; política heredada y evaluada aquí.',
                          'regla_sensibilidad':'Descartar TODAS las filas cuya X tiene etiquetas contradictorias en el corpus completo; luego deduplicar X sin mirar y.',
                          'advertencia':'El descarte usa etiquetas del corpus entero como limpieza de benchmark; NO puede simularse en un nuevo proyecto sin y. Resultados solo análisis de sensibilidad.'}


def build_cohorts(original,out_dir):
    out_dir=Path(out_dir)
    primary, r_primary, s_primary=base.deduplicar_global(original)
    reduced,s_conf=contradiction_audit(original,out_dir/'auditoria')
    sensitivity,r_sens,s_sens=base.deduplicar_global(reduced)
    for name,data in [('principal_deduplicada',primary),('eliminar_grupos_conflictivos',sensitivity)]:
        audit=base.overlap_audit(data)
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
            'huella_principal':base.firma_datos(primary),
            'huella_sensibilidad':base.firma_datos(sensitivity)}
    json_save(out_dir/'auditoria'/'resumen_cohortes.json',report)
    return {'sin_deduplicar':original,'principal_deduplicada':primary,
            'eliminar_grupos_conflictivos':sensitivity},report


def safe_areas(y,c,orders, fraction):
    """Popt normalizado: (A_metodo-A_worst)/(A_opt-A_worst).
    A hasta fracción de LOC con interpolación LINEAL para curva, no inspección
    real de una fracción de módulo; además se reporta recall de módulos completos.
    """
    lines={key:base.curva_esfuerzo(y,c,order) for key,order in orders.items()}
    a_opt=base.area_hasta(*lines['OPT_teorico'],fin=fraction)
    a_worst=base.area_hasta(*lines['WORST_teorico'],fin=fraction)
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
                xs,ys=base.curva_esfuerzo(y,loc_cost,order)
                cost_used=np.cumsum(loc_cost[order])
                complete=int(np.searchsorted(cost_used,budget,side='right'))
                values.append(float(y[order[:complete]].sum()/positive))
                reals.append(float(np.interp(f,xs,ys)))
                areas.append(base.area_hasta(xs,ys,fin=.2))
                areas_full.append(base.area_hasta(xs,ys,fin=1.0))
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
    for target in base.PROJECTS:
        src=[p for p in base.PROJECTS if p!=target]
        Xt,yt=base.pack(data,src)
        Xo,yo=data[target]
        for scenario in configs:
            print(f'[{cohort}] prueba LOPO fija · {target} · {scenario}',flush=True)
            pipe=base.make_pipeline(scenario,'SVM')
            start=time.perf_counter()
            pipe.fit(Xt,yt)
            t_fit=time.perf_counter()-start
            start=time.perf_counter()
            m,score,pred=base.metrics(pipe,Xo,yo)
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


def evaluate_reference_nested(data,cohort,configs_by_project,result_dir):
    """NO reoptimiza las 27 recetas: reutiliza selecciones anidadas de un experimento anterior
    únicamente si hashes de CSV y firma de la cohorte coinciden con las huellas incorporadas.
    Reentrena la receta preseleccionada SIN tocar etiquetas del proyecto test.
    """
    rows=[]; ranks=[]
    for p in base.PROJECTS:
        scenario=configs_by_project[p]['escenario'];algo=configs_by_project[p]['algoritmo']
        src=[q for q in base.PROJECTS if q!=p]
        Xtr,ytr=base.pack(data,src); Xte,yte=data[p]
        print(f'[Selección previa {cohort}] TEST {p}: {algo} / {scenario}',flush=True)
        pipe=base.make_pipeline(scenario,algo)
        pipe.fit(Xtr,ytr)
        m,score,_=base.metrics(pipe,Xte,yte)
        rows.append({'cohorte':cohort,'proyecto':p,'algoritmo':algo,'escenario':scenario,**m})
        ranks.extend(ranking_evaluation(yte,score,Xte['loc'],project=p,cohort=cohort,
                                        procedimiento='seleccion_previa_reentrenada'))
    result_dir=Path(result_dir);result_dir.mkdir(parents=True,exist_ok=True)
    rr=pd.DataFrame(rows);qq=pd.DataFrame(ranks)
    rr.to_csv(result_dir/'seleccion_previa_resultados_por_proyecto.csv',index=False)
    qq.to_csv(result_dir/'seleccion_previa_metricas_QA.csv',index=False)
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


def export_model_candidates(data,root,source_hashes):
    """EXPORTA CANDIDATOS, NO DESPLIEGA. Modelos entrenados con 5 proyectos.
    Estos pipelines no tienen prueba con un sexto proyecto no visto.
    """
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    X,y=base.pack(data,base.PROJECTS)
    report=[]
    for scen in ['E6_ADASYN_MI','E7_SMOTE_RF']:
        dest=root/scen;dest.mkdir(parents=True,exist_ok=True)
        pipe=base.make_pipeline(scen,'SVM');pipe.fit(X,y)
        manifest={'protocolo':EXPERIMENTO_ID,'nombre':'Modelo_general_CPDP',
                  'algoritmo':'SVM','escenario':scen,'columnas':list(base.FEATURES),
                  'version_modelo':f'{EXPERIMENTO_ID}_{scen}',
                  'dataset_fuentes_sha256':source_hashes,'datos_entrenamiento_cantidad':len(y),
                  'huella_datos_entrenados':base.firma_datos(data),
                  'score_tipo':'margen_svm_no_calibrado',
                  'documentally_verified':False,'candidato_no_desplegado':True,
                  'limite':'Sin sexto proyecto independiente. Requiere verificación Streamlit + P01-P08.',
                  'creado_utc':datetime.now(timezone.utc).isoformat()}
        bundle={'pipeline':pipe,'manifest':manifest,'columnas':list(base.FEATURES)}
        path=dest/'modelo_general_cpdp.joblib'
        joblib.dump(bundle,path,compress=3)
        loaded=joblib.load(path)
        assert loaded['manifest']['escenario']==scen
        assert list(loaded['columnas'])==list(base.FEATURES)
        test=loaded['pipeline'].predict(X.iloc[:5])
        assert len(test)==5
        base.jdump(dest/'manifiesto_modelo_general.json',manifest)
        base.jdump(dest/'integridad_exportacion.json',{'sha256_modelo':base.sha256(path),
                             'sha256_manifiesto':base.sha256(dest/'manifiesto_modelo_general.json'),
                             'no_reemplazar_produccion_sin_aprobacion':True})
        report.append({'escenario':scen,'filas_train':len(y),'sha256':base.sha256(path),
                       'estado':'CANDIDATO_NO_DESPLEGADO'})
    pd.DataFrame(report).to_csv(root/'candidatos_exportados.csv',index=False)
    base.jdump(root/'decision_modelo.json',{
       'estado':'PENDIENTE_REVISAR_CON_ASESOR','configuracion_actual_streamlit':'E6_ADASYN_MI',
       'configuracion_previa_seleccionada':'E6_ADASYN_MI',
       'nota':'Wilcoxon con 5 proyectos tiene poca potencia. No significancia NO demuestra equivalencia. Evitar seleccionar en base al test externo. La decisión requiere regla documentada, análisis de estabilidad/costo y pruebas de integración.'})
    return pd.DataFrame(report)


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
    print('Pruebas rápidas: OK (ranking, LOC, Popt y presupuestos).')
