"""Priorización por probabilidad CALIBRADA / LOC, sin usar etiquetas del proyecto test.

Calibración por proyecto fuente: en cada uno de los cuatro proyectos fuente se
predice con un SVM E6 ajustado solo en los otros tres. Con los márgenes OOF
(out-of-fold) y sus etiquetas se ajusta una regresión logística sigmoide
(Platt como mapeo). Luego se reentrena E6 en los cuatro proyectos fuente.
El proyecto objetivo no participa ni en los ajustes ni en la calibración.

No cambia el modelo del prototipo; este procedimiento se usa para evaluar
priorización. El resultado es exploratorio: se conocían datos anteriores.
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, average_precision_score, roc_auc_score
import cpdp_core as base
import cpdp_evaluacion as evaluacion

SEED = base.SEED
BUDGET = 0.20
CALIBRATION_METHOD = 'sigmoide_logistica_en_margenes_OOF_por_proyecto'
METHODS = ['ML_margen_SVM','ML_prob_calibrada','ML_prob_calibrada_por_LOC',
           'ManualUp','LOC_desc','Aleatorio_esperado']


def registrar_plan_analisis(out_dir):
    """Registrar antes de esta ejecución; NO afirmar preregistro histórico."""
    out_dir = Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    plan = {
        'caracter': 'Analisis adicional exploratorio formulado tras conocer resultados de cinco proyectos; no confirmatorio ni preregistrado',
        'modelo_fijo': 'E6_ADASYN_MI / SVM',
        'proyectos': list(base.PROJECTS),
        'cohorte_primaria': 'principal_deduplicada: una X global representativa sin consultar y',
        'estrategia_nueva': 'mayor probabilidad calibrada de defecto dividida entre max(LOC, 1)',
        'calibracion': CALIBRATION_METHOD,
        'comparacion_primaria_nueva': 'ML_prob_calibrada_por_LOC frente a ManualUp, Recall@20 % LOC, modulos completos',
        'indicadores_secundarios': ['Recall@10 % LOC','Recall@30 % LOC','Recall@20 % modulos','Popt normalizado 0-20','Popt normalizado 0-100','Brier de calibracion'],
        'unidad_primaria': 'proyecto (cinco proyectos independientes a nivel conceptual, con amenazas de calidad NASA)',
        'resumen_descriptivo': ['diferencia por proyecto','mediana','numero de proyectos con diferencia positiva','intervalo bootstrap por proyecto'],
        'criterio_descriptivo_estricto': 'Cinco de cinco deltas positivos; para apoyo adicional, limite inferior bootstrap de cada proyecto > 0',
        'limitaciones': ['El intervalo bootstrap re-muestrea modulos y condiciona en los modelos entrenados; no captura incertidumbre por nuevos proyectos.',
                        'Cinco proyectos no permiten concluir superioridad estadistica con Wilcoxon bilateral exacto al 5%.',
                        'No cambiar retrospectivamente el criterio primario del plan original; documentar este analisis adicional como desviacion motivada por observacion del asesor.',
                        'El costo LOC es una aproximacion del esfuerzo de QA, no un tiempo real medido.']}
    evaluacion.json_save(out_dir/'plan_analisis_estrategia_esfuerzo.json',plan)
    return plan


def calibrar_en_fuentes(cohortes, proyecto_objetivo):
    """Devuelve los scores de TEST; calibración solo con cuatro proyectos fuente."""
    fuentes = [p for p in base.PROJECTS if p != proyecto_objetivo]
    assert len(fuentes)==4 and proyecto_objetivo not in fuentes
    oof_scores=[];oof_y=[];tablas_cal=[]
    tic=time.perf_counter()
    for proyecto_cal in fuentes:
        entrena=[p for p in fuentes if p!=proyecto_cal]
        assert proyecto_objetivo not in entrena and proyecto_cal not in entrena
        Xent,yent=base.pack(cohortes,entrena)
        Xcal,ycal=cohortes[proyecto_cal]
        svm=base.make_pipeline('E6_ADASYN_MI','SVM')
        svm.fit(Xent,yent)
        margenes=np.asarray(svm.decision_function(Xcal),dtype=float)
        if not np.isfinite(margenes).all():
            raise ValueError('Margenes no finitos en calibracion')
        oof_scores.append(margenes)
        oof_y.append(np.asarray(ycal,dtype=int))
        tablas_cal.append({'proyecto_objetivo':proyecto_objetivo,
            'proyecto_calibracion':proyecto_cal,'proyectos_entrenamiento':','.join(entrena),
            'n_calibracion':len(ycal),'positivos_calibracion':int(ycal.sum())})
    xx=np.concatenate(oof_scores).reshape(-1,1)
    yy=np.concatenate(oof_y)
    if len(np.unique(yy))!=2:
        raise ValueError('La calibracion requiere ambas clases')
    calibrador=LogisticRegression(solver='lbfgs',max_iter=2000,C=1.0,
                                 random_state=SEED)
    calibrador.fit(xx,yy)
    Xtrain,ytrain=base.pack(cohortes,fuentes)
    Xtest,ytest=cohortes[proyecto_objetivo]
    modelo_final=base.make_pipeline('E6_ADASYN_MI','SVM')
    modelo_final.fit(Xtrain,ytrain)
    scores=np.asarray(modelo_final.decision_function(Xtest),dtype=float)
    prob=np.asarray(calibrador.predict_proba(scores.reshape(-1,1))[:,1],dtype=float)
    if not np.isfinite(prob).all() or np.any((prob<0)|(prob>1)):
        raise ValueError('Probabilidades calibradas fuera del rango [0,1]')
    metadatos={'proyecto':proyecto_objetivo,'fuentes_calibracion':','.join(fuentes),
       'n_OOF_calibrador':int(len(yy)),
       'n_positivos_OOF':int(yy.sum()),
       'coeficiente_sigmoide':float(calibrador.coef_[0,0]),
       'intercepto_sigmoide':float(calibrador.intercept_[0]),
       'segundos_ajuste_y_calibracion':float(time.perf_counter()-tic),
       'brier_test':float(brier_score_loss(np.asarray(ytest,dtype=int),prob)),
       'ap_test_prob_calibrada':float(average_precision_score(ytest,prob)),
       'auc_test_prob_calibrada':float(roc_auc_score(ytest,prob)),
       'advertencia':'Calibrador entrenado con OOF de fuentes; el proyecto test nunca interviene. Brier test reporta calibracion, no valida un nuevo proyecto externo.'}
    return scores,prob,metadatos,tablas_cal


def ranking_con_presupuesto(y,loc,puntuacion,presupuesto=BUDGET,ascendente=False):
    """Recall de módulos COMPLETOS; costo mínimo por módulo = 1 LOC."""
    y=np.asarray(y,dtype=int);loc=np.maximum(np.asarray(loc,dtype=float),1.)
    score=np.asarray(puntuacion,dtype=float)
    if not (len(y)==len(loc)==len(score)) or len(y)==0:
        raise ValueError('longitud incompatible')
    if not np.isfinite(loc).all() or not np.isfinite(score).all():
        raise ValueError('puntuacion/LOC no finitos')
    if y.sum()==0:
        return np.nan
    ids=np.arange(len(y))
    orden=np.lexsort((ids,score if ascendente else -score))
    presupuesto_loc=presupuesto*float(loc.sum())
    usados=np.cumsum(loc[orden])
    completos=int(np.searchsorted(usados,presupuesto_loc,side='right'))
    return float(y[orden[:completos]].sum()/y.sum())


def bootstrap_delta_proyecto(y,loc,p,iteraciones=1000,seed=SEED):
    """Intervalo condicional: remuestrea módulos, no reentrena el modelo.

    Si una réplica no contiene defectos, se descarta; se documenta cuántas.
    """
    y=np.asarray(y,dtype=int);loc=np.maximum(np.asarray(loc,dtype=float),1.)
    p=np.asarray(p,dtype=float)
    rng=np.random.default_rng(seed)
    deltas=[];omitidos=0
    for _ in range(iteraciones):
        idx=rng.integers(0,len(y),size=len(y))
        ys=y[idx];ls=loc[idx];ps=p[idx]
        if ys.sum()==0:
            omitidos+=1;continue
        a=ranking_con_presupuesto(ys,ls,ps/ls)
        b=ranking_con_presupuesto(ys,ls,ls,ascendente=True)
        deltas.append(a-b)
    if len(deltas)<int(.95*iteraciones):
        raise ValueError('Demasiadas replicas sin positivos para bootstrap estable')
    return {'bootstrap_repeticiones':int(iteraciones),
            'bootstrap_replicas_validas':len(deltas),
            'bootstrap_replicas_sin_positivos':omitidos,
            'IC95_delta_inferior':float(np.quantile(deltas,.025)),
            'IC95_delta_superior':float(np.quantile(deltas,.975)),
            'nota_IC':'Remuestreo de modulos condicionado en scores fijos; no representa incertidumbre entre proyectos ni reentrenamiento.'}


def ejecutar(cohortes,cohorte,root,bootstrap=1000):
    """Comparación primaria de probabilidad/LOC con ManualUp y controles."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    scores_por_proyecto=[];ranking=[];calibraciones=[];cal_folds=[];intervalos=[]
    for proyecto in base.PROJECTS:
        print('Calibración y evaluación E6 por esfuerzo:',cohorte,proyecto,flush=True)
        margen,prob,meta,folds=calibrar_en_fuentes(cohortes,proyecto)
        Xtest,ytest=cohortes[proyecto]
        y=np.asarray(ytest,dtype=int)
        loc=np.maximum(np.asarray(Xtest['loc'],dtype=float),1.)
        densidad=prob/loc
        registro=pd.DataFrame({'proyecto':proyecto,'indice_local':np.arange(len(y)),
            'etiqueta_defecto':y,'loc_costo':loc,'margen_SVM_E6':margen,
            'probabilidad_defecto_calibrada':prob,'riesgo_por_LOC':densidad})
        scores_por_proyecto.append(registro)
        calibraciones.append(meta);cal_folds.extend(folds)
        for nombre,scores in [('ML_margen_SVM',margen),
                              ('ML_prob_calibrada',prob),
                              ('ML_prob_calibrada_por_LOC',densidad)]:
            filas=evaluacion.ranking_evaluation(y,scores,loc,project=proyecto,
                    cohort=cohorte,procedimiento='E6_calibrado_por_proyectos',random_repeats=50)
            for row in filas:
                if row['metodo']=='ML':
                    row['metodo']=nombre;ranking.append(row)
                elif nombre=='ML_margen_SVM':
                    ranking.append(row)  # ManualUp, LOC-desc, aleatorio: solo una vez.
        ci=bootstrap_delta_proyecto(y,loc,prob,iteraciones=bootstrap,
                seed=SEED+sum(ord(x) for x in proyecto))
        intervalos.append({'proyecto':proyecto,'cohorte':cohorte,**ci})
    pred=pd.concat(scores_por_proyecto,ignore_index=True)
    tablas=pd.DataFrame(ranking)
    cal_df=pd.DataFrame(calibraciones)
    ci_df=pd.DataFrame(intervalos)
    pred.to_csv(root/'predicciones_por_proyecto.csv',index=False)
    tablas.to_csv(root/'ranking_por_proyecto_y_presupuesto.csv',index=False)
    cal_df.to_csv(root/'calibracion_por_proyecto.csv',index=False)
    pd.DataFrame(cal_folds).to_csv(root/'folds_calibracion_solo_fuentes.csv',index=False)
    ci_df.to_csv(root/'IC95_por_proyecto.csv',index=False)
    summary=(tablas.groupby(['metodo','presupuesto_fraccion'],as_index=False)
        [['recall_por_modulos','recall_por_LOC_modulos_completos',
          'popt_normalizado_0_20','popt_normalizado_0_100']].mean())
    summary.to_csv(root/'resumen_macro_por_metodo_y_presupuesto.csv',index=False)
    # Contraste por proyecto de la métrica operacional 20 % LOC.
    focus=tablas[np.isclose(tablas.presupuesto_fraccion,BUDGET)]
    pivot=focus.pivot(index='proyecto',columns='metodo',values='recall_por_LOC_modulos_completos')
    per=pd.DataFrame({'proyecto':pivot.index,
          'ML_margen':pivot['ML_margen_SVM'].to_numpy(),
          'ML_probabilidad':pivot['ML_prob_calibrada'].to_numpy(),
          'ML_probabilidad_por_LOC':pivot['ML_prob_calibrada_por_LOC'].to_numpy(),
          'ManualUp':pivot['ManualUp'].to_numpy(),
          'LOC_desc':pivot['LOC_desc'].to_numpy()})
    per['delta_ML_calibrado_por_LOC_menos_ManualUp']=per['ML_probabilidad_por_LOC']-per['ManualUp']
    per=per.merge(ci_df[['proyecto','IC95_delta_inferior','IC95_delta_superior']],on='proyecto',how='left',validate='one_to_one')
    per.to_csv(root/'diferencias_20pct_LOC_por_proyecto.csv',index=False)
    d=per['delta_ML_calibrado_por_LOC_menos_ManualUp'].to_numpy()
    criterio=bool(np.all(d>0) and np.all(per['IC95_delta_inferior']>0))
    informe={'comparacion':'ML_prob_calibrada_por_LOC menos ManualUp en Recall@20% LOC',
          'cohorte':cohorte,'n_proyectos':5,
          'promedio_ml_calibrado_por_loc':float(per.ML_probabilidad_por_LOC.mean()),
          'promedio_manualup':float(per.ManualUp.mean()),
          'mediana_delta':float(np.median(d)),
          'media_delta':float(np.mean(d)),
          'proyectos_delta_positivo':int(np.sum(d>0)),
          'proyectos_delta_negativo':int(np.sum(d<0)),
          'proyectos_empate':int(np.sum(d==0)),
          'cumple_criterio_descriptivo_estricto':criterio,
          'advertencia':'Resultado exploratorio. No constituye prueba de superioridad externa ni se cambia el criterio segun el resultado; delta por proyecto e IC condicionales.'}
    evaluacion.json_save(root/'decision_descriptiva.json',informe)
    # Imagen comparativa y gráfica de diferencias con CI por proyecto.
    fig,ax=plt.subplots(figsize=(10,5))
    for nombre in ['ML_margen_SVM','ML_prob_calibrada','ML_prob_calibrada_por_LOC','ManualUp']:
        subset=summary[summary.metodo==nombre].sort_values('presupuesto_fraccion')
        ax.plot(subset.presupuesto_fraccion.to_numpy()*100,
                subset.recall_por_LOC_modulos_completos.to_numpy()*100,
                marker='o',label=nombre)
    ax.set(title='Priorización E6 frente a ManualUp (presupuesto en LOC)',
           xlabel='Presupuesto de LOC inspeccionadas (%)',
           ylabel='Recall de módulos defectuosos (%)')
    ax.grid(alpha=.3);ax.legend(fontsize=8);fig.tight_layout()
    fig.savefig(root/'curvas_recall_LOC.png',dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5))
    xs=np.arange(len(per));vs=per.delta_ML_calibrado_por_LOC_menos_ManualUp.to_numpy()*100
    lower=(per.delta_ML_calibrado_por_LOC_menos_ManualUp-per.IC95_delta_inferior).to_numpy()*100
    upper=(per.IC95_delta_superior-per.delta_ML_calibrado_por_LOC_menos_ManualUp).to_numpy()*100
    ax.errorbar(xs,vs,yerr=np.vstack([np.maximum(lower,0),np.maximum(upper,0)]),
                fmt='o',capsize=4)
    ax.axhline(0,color='gray',linestyle='--')
    ax.set_xticks(xs,labels=per.proyecto.to_list())
    ax.set(xlabel='Proyecto reservado',ylabel='Δ Recall@20 % LOC (puntos porcentuales)',
           title='ML calibrado/LOC menos ManualUp; IC 95 % bootstrap condicional')
    ax.grid(axis='y',alpha=.3);fig.tight_layout()
    fig.savefig(root/'delta_por_proyecto_IC95.png',dpi=180)
    plt.close(fig)
    return per,summary,cal_df,informe


def selfcheck():
    y=np.array([0,1,0,1,0,1,0,0,1],dtype=int)
    loc=np.array([100,2,80,3,20,4,50,10,5],dtype=float)
    prob=np.array([.2,.7,.1,.9,.2,.5,.8,.1,.75])
    base_recall=ranking_con_presupuesto(y,loc,loc,ascendente=True)
    new_recall=ranking_con_presupuesto(y,loc,prob/loc)
    assert 0<=base_recall<=1 and 0<=new_recall<=1
    ci=bootstrap_delta_proyecto(y,loc,prob,iteraciones=100,seed=SEED)
    assert ci['bootstrap_replicas_validas']>90
    print('Pruebas unitarias de presupuesto, ranking y bootstrap: OK')
