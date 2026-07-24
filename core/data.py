"""Carregamento, enriquecimento e filtragem da base de vendas."""

from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "vendas_tratadas.csv"

DIAS_PT = {
    "Monday": "Segunda",
    "Tuesday": "Terça",
    "Wednesday": "Quarta",
    "Thursday": "Quinta",
    "Friday": "Sexta",
    "Saturday": "Sábado",
    "Sunday": "Domingo",
}
ORDEM_DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}
ORDEM_PERIODOS = ["Manha", "Tarde", "Noite"]

# Regras de inferência de categoria a partir do nome do produto (aplicadas em ordem)
_REGRAS_CATEGORIA = [
    (("fant",), "Fantasia"),
    (("conjunto",), "Conjunto"),
    (("vestido",), "Vestido"),
    (("camisa", "camiseta", "blusa", "colete", "body"), "Camisas & Coletes"),
    (("calça", "calcinha", "cueca", "short", "bermuda", "saia", "salopete", "legging", "macacão"), "Vestuário"),
    (("laço", "faixa", "tiara", "meia", "bolsa", "arco", "papel", "presente", "asa", "varinha", "coroa", "máscara", "mascara", "luva", "sapat", "tênis", "tenis"), "Acessórios"),
]


def _inferir_categoria(produto: str) -> str:
    nome = str(produto).lower()
    for termos, categoria in _REGRAS_CATEGORIA:
        if any(t in nome for t in termos):
            return categoria
    return "Outros"


@st.cache_data(show_spinner="Carregando base de vendas...")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    df["Data_Hora"] = pd.to_datetime(df["Data_Hora"], errors="coerce")
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data_Hora", "Subtotal"])

    # Enriquecimento em português para todos os gráficos
    df["Dia_Semana_PT"] = df["Dia_da_Semana"].map(DIAS_PT)
    df["Mes_Nome"] = df["Mes"].map(MESES_PT)
    df["Ano_Mes"] = df["Data_Hora"].dt.to_period("M").dt.to_timestamp()

    # Categoria: mantém a original quando existe, senão infere pelo nome do produto
    df["Categoria"] = df["Categoria"].fillna(df["Produto"].map(_inferir_categoria))

    return df


def periodo_dados(df: pd.DataFrame) -> str:
    ini = df["Data"].min().strftime("%d/%m/%Y")
    fim = df["Data"].max().strftime("%d/%m/%Y")
    return f"{ini} a {fim}"


def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Filtros globais na sidebar, compartilhados por todas as páginas."""
    st.sidebar.markdown("## 🎛️ Filtros")

    dmin, dmax = df["Data"].min().date(), df["Data"].max().date()
    periodo = st.sidebar.date_input(
        "Período",
        value=(dmin, dmax),
        min_value=dmin,
        max_value=dmax,
        format="DD/MM/YYYY",
        key="flt_periodo",
    )

    categorias = st.sidebar.multiselect(
        "Categoria",
        options=sorted(df["Categoria"].dropna().unique()),
        default=None,
        placeholder="Todas as categorias",
        key="flt_categoria",
    )
    pagamentos = st.sidebar.multiselect(
        "Forma de pagamento",
        options=sorted(df["Forma_de_Pagamento_Simples"].dropna().unique()),
        default=None,
        placeholder="Todas as formas",
        key="flt_pagamento",
    )

    out = df
    if isinstance(periodo, tuple) and len(periodo) == 2:
        ini, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
        out = out[(out["Data"] >= ini) & (out["Data"] <= fim)]
    if categorias:
        out = out[out["Categoria"].isin(categorias)]
    if pagamentos:
        out = out[out["Forma_de_Pagamento_Simples"].isin(pagamentos)]

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"**{len(out):,}** itens vendidos no recorte atual "
        f"({len(out) / len(df) * 100:.0f}% da base)".replace(",", ".")
    )
    st.sidebar.caption("Dashboard Executivo · DKidsFantasias")

    return out
