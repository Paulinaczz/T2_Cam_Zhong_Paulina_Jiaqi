from pathlib import Path
from io import BytesIO
import pandas as pd
import pytest
from pds.validation import read_csv_bytes, validate_input
from pds.errors import InputError

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'sample'/'ejemplo_carga.csv'
FEATURES=pd.read_csv(ROOT/'data'/'sample'/'plantilla_para_streamlit.csv',nrows=0).columns.tolist()[1:]


def read_ok():
    raw=read_csv_bytes(DATA.read_bytes(),'ejemplo.csv')
    return validate_input(raw,FEATURES,DATA.read_bytes(),'ejemplo.csv')


def test_example_valid_21_metrics():
    item=read_ok()
    assert len(item.features.columns)==21
    assert len(item.features)==18
    assert item.identifiers.nunique()==18


def test_missing_required_column():
    raw=pd.read_csv(DATA).drop(columns=['loc'])
    with pytest.raises(InputError,match='Faltan métricas'):
        validate_input(raw,FEATURES)


def test_header_alias():
    raw=pd.read_csv(DATA).rename(columns={'locCodeAndComment':'lOCodeAndComment'})
    result=validate_input(raw,FEATURES)
    assert 'locCodeAndComment' in result.features.columns


def test_duplicate_ids():
    raw=pd.read_csv(DATA)
    raw.loc[1,'id_modulo']=raw.loc[0,'id_modulo']
    with pytest.raises(InputError,match='repetidos'):
        validate_input(raw,FEATURES)


def test_unknown_extra_column():
    raw=pd.read_csv(DATA)
    raw['mi_extracolumna']=23
    with pytest.raises(InputError,match='Columnas no admitidas'):
        validate_input(raw,FEATURES)


def test_inf_rejected():
    raw=pd.read_csv(DATA)
    raw.loc[0,'loc']='inf'
    with pytest.raises(InputError,match='infinitos'):
        validate_input(raw,FEATURES)


def test_non_numeric_rejected():
    raw=pd.read_csv(DATA)
    raw.loc[1,'v']='palabra'
    with pytest.raises(InputError,match='no numéricos'):
        validate_input(raw,FEATURES)


def test_optional_target_ignored():
    raw=pd.read_csv(DATA)
    raw['defects']=1
    validated=validate_input(raw,FEATURES)
    assert len(validated.features.columns)==21
    assert any('etiquetas' in w for w in validated.warnings)


def test_without_id_generated():
    raw=pd.read_csv(DATA).drop(columns=['id_modulo'])
    validated=validate_input(raw,FEATURES)
    assert validated.identifiers.iloc[0].startswith('modulo_')


def test_bad_extension_rejected():
    with pytest.raises(InputError,match='extensión'):
        read_csv_bytes(DATA.read_bytes(),'archivo.xlsx')
