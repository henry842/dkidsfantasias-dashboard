import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="DKidsFantasias - Dashboard", layout="wide")
st.title("🎭 DKidsFantasias - Dashboard Executivo de Vendas")

# Caminho do CSV padronizado
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "vendas_tratadas.csv"

# Carregar os dados apenas se ainda não estiverem no session_state
if 'df' not in st.session_state:
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip()
        if "Data_Hora" in df.columns:
            df["Data_Hora"] = pd.to_datetime(df["Data_Hora"], errors="coerce")
        st.session_state.df = df
        st.success("✅ Dataset carregado com sucesso!")
    else:
        st.error("⚠️ Arquivo de dados não encontrado!")
        st.stop()
