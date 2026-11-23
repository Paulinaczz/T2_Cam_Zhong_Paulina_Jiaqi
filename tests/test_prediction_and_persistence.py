from pathlib import Path
import pandas as pd
import numpy as np
from pds.model import ModelArtifact
from pds.prediction import predict, csv_results, SCORE_TYPE, compare_strategies, csv_comparison_results, calibrate_probabilities
from pds.persistence import init_db, register_execution, list_executions, get_execution
from pds.validation import validate_input
from pds.errors import ModelError

ROOT=Path(__file__).resolve().parents[1]
FEATURES=pd.read_csv(ROOT/'data'/'sample'/'plantilla_para_streamlit.csv',nrows=0).columns.tolist()[1:]

class Classifier:
    classes_=np.array([0,1])

class FakePipeline:
    named_steps={'model':Classifier()}
    def decision_function(self,X):
        return np.linspace(-2.0, 2.0, len(X))
    def predict(self,X):
        return (self.decision_function(X) > 0).astype(int)

def fixture_result():
    raw=pd.read_csv(ROOT/'data'/'sample'/'ejemplo_carga.csv').head(6)
    data=validate_input(raw,FEATURES)
    model=ModelArtifact(FakePipeline(),{'columnas':FEATURES,'protocolo':'test','algoritmo':'SVM','escenario':'E6_ADASYN_MI'},'f'*64,Path('fake.joblib'))
    return data,model,predict(data,model)

def test_rank_and_classes():
    data,model,result=fixture_result()
    assert result.prioridad.tolist()==[1,2,3,4,5,6]
    assert result.score_riesgo.is_monotonic_decreasing
    assert set(result.clase_predicha)=={0,1}
    assert set(result.tipo_score)=={SCORE_TYPE}
    assert len(result)==len(data.features)


def test_csv_formula_injection_escaped():
    data,model,result=fixture_result()
    result.loc[0,'id_modulo']='=1+2'
    out=csv_results(result).decode('utf-8-sig')
    assert "'=1+2" in out


def test_sqlite_record_and_read(tmp_path):
    db=tmp_path/'traces.sqlite3'
    data,model,result=fixture_result()
    init_db(db)
    execution_id=register_execution(db,data,model,result)
    history=list_executions(db)
    assert len(history)==1
    assert history.iloc[0].total_registros==6
    meta,saved=get_execution(db,execution_id)
    assert len(saved)==6
    assert meta['sha256_modelo']==model.sha256
    assert saved.prioridad.tolist()==list(range(1,7))


def test_strategy_comparison_and_calibration():
    data, model, _ = fixture_result()
    comp = compare_strategies(data, model)
    assert len(comp) == len(data.features)
    assert set(comp["prioridad_operativa_svm"]) == set(range(1, len(data.features) + 1))
    assert set(comp["prioridad_experimental_calibrada_loc"]) == set(range(1, len(data.features) + 1))
    assert set(comp["prioridad_referencia_manualup"]) == set(range(1, len(data.features) + 1))
    assert (comp["probabilidad_calibrada"] >= 0.0).all() and (comp["probabilidad_calibrada"] <= 1.0).all()
    assert (comp["densidad_riesgo_loc"] > 0.0).all()

    # Sanitización de fórmulas en exportación comparativa
    comp.loc[0, "id_modulo"] = "=2+3"
    csv_bytes = csv_comparison_results(comp)
    assert "'=2+3" in csv_bytes.decode("utf-8-sig")
