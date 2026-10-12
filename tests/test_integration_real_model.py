"""Ejecutar con el entorno exacto de Colab v11 (scikit-learn==1.6.1)."""
from pathlib import Path
from importlib.metadata import version
import pytest

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.skipif(version('scikit-learn')!='1.6.1' or version('imbalanced-learn')!='0.14.2', reason='requiere dependencias exactas v11')
def test_real_pipeline_predicts_csv():
    from pds.model import load_model
    from pds.service import prepare_csv
    from pds.prediction import predict
    model=load_model(ROOT/'artifacts/models')
    data=(ROOT/'data/sample/ejemplo_carga.csv').read_bytes()
    valid=prepare_csv(data,'ejemplo.csv',model)
    out=predict(valid,model)
    assert len(out)==18
    assert out['score_riesgo'].notna().all()
