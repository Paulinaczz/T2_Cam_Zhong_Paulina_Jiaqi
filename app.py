"""PDS-QA: aplicación Streamlit para priorización de módulos por riesgo estimado.

Solo carga el pipeline local confiable de la tesis. No entrena modelos ni recibe código fuente.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import pandas as pd
import streamlit as st

from src.pds.errors import PDSError
from src.pds.model import load_model
from src.pds.persistence import init_db, list_executions, get_execution
from src.pds.prediction import csv_results
from src.pds.service import prepare_csv, run_analysis

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "artifacts" / "models"
DB_PATH = Path(os.environ.get("PDS_DB_PATH", str(ROOT / "data" / "runtime" / "pds.sqlite3")))
TEMPLATE_PATH = ROOT / "data" / "sample" / "plantilla_para_streamlit.csv"
SAMPLE_PATH = ROOT / "data" / "sample" / "ejemplo_carga.csv"

st.set_page_config(page_title="PDS | Aseguramiento de calidad", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:2rem;max-width:1180px}
[data-testid="stSidebar"]{background-color:#11253a}
[data-testid="stSidebar"] *{color:#f0f5fc!important}
.stButton>button[kind="primary"]{background:#176a75;border:0}
.small-note{color:#73808d;font-size:.82rem}
</style>""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Verificando modelo entrenado...")
def artifact():
    return load_model(MODEL_DIR)

@st.cache_resource(show_spinner=False)
def database_ready():
    init_db(DB_PATH)
    return True


def heading(kicker, title, desc):
    st.caption(kicker)
    st.title(title)
    st.write(desc)


def move(page):
    st.session_state["pagina"] = page
    st.rerun()


def summary_cards(data):
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Módulos analizados", len(data))
    positives=int(data["clase_predicha"].sum())
    c2.metric("Clasificados con riesgo", positives)
    c3.metric("Clasificados sin riesgo",len(data)-positives)
    c4.metric("Puntaje máximo",f"{data['score_riesgo'].max():.3f}")


# Bloquea startup antes de deserializar si las dependencias no coinciden.
try:
    model=artifact()
    database_ready()
except PDSError as ex:
    st.error(f"No se puede iniciar el prototipo: {ex}")
    st.info("Consulta el README para instalar las versiones exactas y restaurar el archivo del modelo original.")
    st.stop()

if "pagina" not in st.session_state:
    st.session_state.pagina="Inicio"
if "resultado" not in st.session_state:
    st.session_state.resultado=None
if "entrada" not in st.session_state:
    st.session_state.entrada=None

pages={
    "Inicio":"UI01 · Inicio y modelo",
    "Carga":"UI02 · Cargar CSV",
    "Validación":"UI03 · Validación",
    "Resultados":"UI04 · Priorización",
    "Historial":"UI05 · Evidencias",
    "Ayuda":"UI06 · Guía de uso"
}
with st.sidebar:
    st.markdown("### 🛡️ PDS · Calidad de software")
    st.caption("PROTOTIPO DE TESIS · PI8")
    keys=list(pages)
    pos=keys.index(st.session_state.pagina) if st.session_state.pagina in keys else 0
    selected=st.radio("Navegación",keys,index=pos,format_func=lambda k: pages[k])
    if selected!=st.session_state.pagina:
        st.session_state.pagina=selected
        st.rerun()
    st.divider()
    st.success("Modelo local verificado")
    st.markdown(f"**{model.manifest['algoritmo']} · {model.manifest['escenario']}**")
    st.caption("21 métricas estáticas compatibles · clasificación binaria")
    st.caption("Sin lectura automática de código fuente ni repositorios")

page=st.session_state.pagina
if page=="Inicio":
    heading("UI01 · VISIÓN GENERAL", "Predicción de defectos para QA",
        "Clasificación y priorización de módulos mediante un modelo histórico de Machine Learning entrenado entre proyectos.")
    st.info("**Objetivo:** orientar la revisión y las pruebas de QA. El sistema estima propensión a defectos; no demuestra la presencia de errores reales.")
    p1,p2,p3=st.columns(3)
    p1.metric("Algoritmo operativo",model.manifest.get("algoritmo","-"))
    p2.metric("Escenario",model.manifest.get("escenario","-"))
    p3.metric("Métricas de entrada",len(model.manifest["columnas"]))
    st.subheader("Flujo de trabajo")
    st.markdown("**1.** Descargar plantilla o preparar un CSV con métricas compatibles.  \n**2.** Subir archivo y validar sus columnas.  \n**3.** Ejecutar inferencia y ordenar módulos para QA.  \n**4.** Exportar CSV y consultar evidencia en SQLite.")
    st.warning("**Interpretación responsable:** los scores de SVM son márgenes de decisión sin calibrar, NO probabilidades del 0–100 %. Una clasificación positiva no confirma que un módulo contenga defectos.")
    c1,c2=st.columns(2)
    with c1: st.download_button("⬇️ Descargar plantilla CSV",data=TEMPLATE_PATH.read_bytes(),file_name="plantilla_metricas_pds.csv",mime="text/csv",use_container_width=True)
    with c2:
        if st.button("Comenzar análisis →",type="primary",use_container_width=True):move("Carga")
    with st.expander("Contexto del experimento científico"):
        st.write("Pipeline final: SVM + SMOTE + selección de características basada en Random Forest; entrenado con CM1, JM1, KC1, KC2 y PC1 tras validación entre proyectos.")
        st.write(f"F1 promedio de selección entre proyectos: **{model.manifest.get('cv_global_f1',0):.3f}**. Este resultado no es una evaluación independiente del archivo final entrenado con los cinco proyectos.")
        st.write("La documentación de procedencia y equivalencias de métricas requiere revisión humana.")

elif page=="Carga":
    heading("UI02 · CARGA DE DATOS", "Sube las métricas de tu proyecto",
        "El CSV debe describir módulos mediante las 21 métricas esperadas. Puedes añadir la columna opcional id_modulo.")
    a,b=st.columns(2)
    with a: st.download_button("Descargar plantilla vacía",data=TEMPLATE_PATH.read_bytes(),file_name="plantilla_metricas_pds.csv",mime="text/csv",use_container_width=True)
    with b: st.download_button("Descargar CSV de ejemplo",data=SAMPLE_PATH.read_bytes(),file_name="ejemplo_carga.csv",mime="text/csv",use_container_width=True)
    st.caption("El ejemplo contiene valores de demostración. No sirve para medir la exactitud científica del modelo.")
    uploaded=st.file_uploader("Selecciona un CSV (máximo 10 MB, 20 000 módulos)",type=["csv"],accept_multiple_files=False)
    if uploaded:
        blob=uploaded.getvalue()
        st.write(f"Archivo: **{uploaded.name}** · {len(blob):,} bytes")
        if st.button("Validar archivo",type="primary"):
            try:
                validated=prepare_csv(blob,uploaded.name,model)
            except PDSError as ex:
                st.session_state.entrada=None
                st.session_state.resultado=None
                st.error(f"No se pudo validar: {ex}")
            else:
                st.session_state.entrada=validated
                st.session_state.resultado=None
                move("Validación")
    with st.expander("¿Qué columnas se admiten?"):
        st.code(", ".join(model.manifest["columnas"]),language="text")
        st.write("Se permite **id_modulo** (opcional). Las columnas de etiquetas históricas `defects` y `problems` se ignoran si están presentes. Cualquier otra columna extra genera un error de esquema.")
        st.write("Las variaciones de mayúsculas y el alias documentado de `lOCodeAndComment` se normalizan. Las métricas deben conservar significados y unidades compatibles.")

elif page=="Validación":
    heading("UI03 · VALIDACIÓN", "Comprobación de compatibilidad",
        "Antes de predecir, el sistema comprueba encabezados, valores numéricos e identificadores.")
    data=st.session_state.entrada
    if data is None:
        st.info("Aún no hay un archivo validado. Ve a «Carga» para subir un CSV.")
        if st.button("Ir a cargar archivo"):move("Carga")
    else:
        st.success("El CSV cumple las validaciones de estructura para este pipeline.")
        c1,c2,c3=st.columns(3)
        c1.metric("Módulos",data.original_rows)
        c2.metric("Métricas verificadas",len(data.features.columns))
        c3.metric("Valores faltantes",int(data.features.isna().sum().sum()))
        st.write("**Huella SHA-256 del archivo de entrada:**")
        st.code(data.sha256,language="text")
        for warning in data.warnings: st.warning(warning)
        with st.expander("Vista previa de métricas (5 filas)"):
            example=data.features.head(5).copy()
            example.insert(0,"id_modulo",data.identifiers.head(5).values)
            st.dataframe(example,use_container_width=True,hide_index=True)
        st.caption("El pipeline incorpora imputación y escalado aprendidos en entrenamiento. SMOTE se empleó solo al ajustar el modelo, no en inferencia.")
        if st.button("▶ Ejecutar predicción y guardar evidencia",type="primary",use_container_width=True):
            try:
                execution_id,result=run_analysis(data,model,DB_PATH)
            except PDSError as ex:
                st.error(f"No se pudo completar la inferencia: {ex}")
            else:
                st.session_state.resultado=(execution_id,result)
                move("Resultados")

elif page=="Resultados":
    heading("UI04 · RESULTADOS", "Ranking para priorizar QA",
        "Los módulos se ordenan de mayor a menor margen SVM estimado. El score NO representa un porcentaje de probabilidad.")
    current=st.session_state.resultado
    if current is None:
        st.info("Primero valida un CSV y ejecuta la predicción en la pantalla anterior.")
        if st.button("Ir a carga"):move("Carga")
    else:
        execution_id,results=current
        summary_cards(results)
        st.caption(f"Ejecución: {execution_id}")
        st.warning("El margen puede ser negativo o positivo. La categoría 'potencialmente defectuoso' es una predicción, no un defecto confirmado.")
        s1,s2=st.columns([2,1])
        with s1:
            show_only=st.checkbox("Mostrar solo módulos clasificados con riesgo",value=False)
        with s2:
            top_n=st.number_input("Máximo de módulos visibles",min_value=1,max_value=len(results),value=min(30,len(results)))
        viewed=results[results["clase_predicha"]==1] if show_only else results
        st.dataframe(viewed.head(int(top_n)),use_container_width=True,hide_index=True)
        st.download_button("⬇️ Exportar ranking completo CSV",csv_results(results),file_name=f"ranking_qa_{execution_id[:8]}.csv",mime="text/csv",type="primary")
        st.subheader("Distribución de las clasificaciones")
        count=(results["interpretacion"].value_counts().rename_axis("categoría").reset_index(name="módulos"))
        st.bar_chart(count.set_index("categoría"))
        if st.button("Ver trazabilidad de ejecución"):move("Historial")

elif page=="Historial":
    heading("UI05 · TRAZABILIDAD", "Historial y evidencia",
        "Registro local SQLite de archivos procesados, modelo utilizado, huellas y predicciones asociadas.")
    try:
        history=list_executions(DB_PATH)
    except Exception:
        st.error("No se pudo consultar la base de datos SQLite")
        st.stop()
    if history.empty:
        st.info("Todavía no hay ejecuciones. Realiza primero una predicción.")
    else:
        st.dataframe(history,use_container_width=True,hide_index=True)
        ids=history["execution_id"].tolist()
        chosen=st.selectbox("Selecciona una ejecución para consultar el detalle",ids)
        details,rows=get_execution(DB_PATH,chosen)
        if details:
            c1,c2,c3=st.columns(3)
            c1.metric("Módulos",details["total_registros"])
            c2.metric("Positivos estimados",details["total_positivos"])
            c3.metric("Estado",details["estado"])
            st.json({k:v for k,v in details.items() if k not in ("total_registros","total_positivos","estado")})
            st.dataframe(rows,use_container_width=True,hide_index=True)
            st.download_button("⬇️ Descargar resultados de esta ejecución",csv_results(rows),file_name=f"evidencia_{chosen[:8]}.csv",mime="text/csv")
    st.caption("En ejecución local los datos se guardan en data/runtime (ignorada por Git). En alojamiento gratuito con disco efímero el historial puede perderse al reiniciar.")

elif page=="Ayuda":
    heading("UI06 · AYUDA", "Guía y limitaciones",
        "Cómo preparar los datos, interpretar los resultados y utilizar el sistema de forma responsable.")
    with st.expander("¿Qué predice exactamente?",expanded=True):
        st.write("Predice si un módulo se parece a módulos históricamente etiquetados como defectuosos, según 21 métricas estáticas. No indica tipo, número, ubicación ni gravedad de un defecto.")
    with st.expander("¿Necesito subir código Java o un repositorio GitHub?"):
        st.write("No. Esta primera versión solo acepta un archivo CSV con métricas extraídas previamente. La extracción automática de código está fuera del alcance actual.")
    with st.expander("¿Qué significa score_riesgo?"):
        st.write("Es el margen de decisión no calibrado de SVM. Es útil para establecer un orden relativo entre módulos bajo este pipeline, pero no debe presentarse como probabilidad porcentual.")
    with st.expander("¿Qué debo revisar si mi CSV es rechazado?"):
        st.write("Verifica que haya 21 métricas numéricas compatibles, encabezados correctos, sin columnas extra (excepto id_modulo, defects o problems) y sin identificadores duplicados.")
    with st.expander("¿Cuál es el alcance de la evaluación científica?"):
        st.write("Los resultados proceden de validación entre cinco proyectos NASA/PROMISE. No garantizan generalización a cualquier proyecto. La evidencia histórica mostró variación por dataset y priorización que no superó consistentemente a LOC.")
    st.caption(f"Modelo: {model.manifest.get('protocolo')} · SHA-256: {model.sha256}")
