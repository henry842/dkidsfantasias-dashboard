"""Visão Executiva — página inicial do dashboard."""

import altair as alt
import streamlit as st

from core import ui
from core.data import ORDEM_DIAS, load_data, periodo_dados, sidebar_filters
from core.insights import insights_executivos, kpis_gerais
from core.ui import ACCENT, PRIMARY, SECONDARY, TEAL, fmt_brl, fmt_int, fmt_pct

ui.inject_css()

base = load_data()
df = sidebar_filters(base)

ui.hero(
    "Visão Executiva de Vendas",
    f"Panorama consolidado do negócio · Dados de {periodo_dados(base)}",
)

if df.empty:
    st.warning("Nenhum dado no recorte selecionado. Ajuste os filtros na barra lateral.")
    st.stop()

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
k = kpis_gerais(df)

delta, direction = None, "neutral"
if k["variacao_mm"] is not None:
    direction = "up" if k["variacao_mm"] >= 0 else "down"
    delta = f"{fmt_pct(abs(k['variacao_mm']))} vs mês anterior"

ui.kpi_row([
    {"label": "Faturamento", "value": fmt_brl(k["faturamento"]), "delta": delta,
     "direction": direction, "accent": PRIMARY},
    {"label": "Vendas realizadas", "value": fmt_int(k["n_vendas"]), "accent": SECONDARY},
    {"label": "Itens vendidos", "value": fmt_int(k["itens"]), "accent": ACCENT},
    {"label": "Ticket médio", "value": fmt_brl(k["ticket_medio"]), "accent": TEAL},
    {"label": "Produtos ativos", "value": fmt_int(k["produtos_ativos"]), "accent": "#4CC9F0"},
])

# ---------------------------------------------------------------------------
# Evolução mensal + mix de categorias
# ---------------------------------------------------------------------------
col_esq, col_dir = st.columns([3, 2], gap="large")

with col_esq:
    ui.section("📈 Evolução mensal do faturamento", "Barras: faturamento · Linha: tendência")
    mensal = df.groupby("Ano_Mes", as_index=False)["Subtotal"].sum()

    barras = alt.Chart(mensal).mark_bar(
        cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=42, color=PRIMARY, opacity=0.85
    ).encode(
        x=alt.X("yearmonth(Ano_Mes):T", title=None, axis=alt.Axis(format="%b/%y", labelAngle=0)),
        y=alt.Y("Subtotal:Q", title="Faturamento (R$)"),
        tooltip=[
            alt.Tooltip("yearmonth(Ano_Mes):T", title="Mês", format="%B/%Y"),
            alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
        ],
    )
    linha = alt.Chart(mensal).mark_line(
        color=SECONDARY, strokeWidth=3, point=alt.OverlayMarkDef(color=SECONDARY, size=70)
    ).encode(
        x="yearmonth(Ano_Mes):T",
        y="Subtotal:Q",
    )
    ui.render(barras + linha, height=330)

with col_dir:
    ui.section("🧩 Faturamento por categoria", "Participação de cada categoria no período")
    cat = df.groupby("Categoria", as_index=False)["Subtotal"].sum()
    cat["Participacao"] = cat["Subtotal"] / cat["Subtotal"].sum() * 100

    donut = alt.Chart(cat).mark_arc(innerRadius=68, cornerRadius=4, padAngle=0.02).encode(
        theta=alt.Theta("Subtotal:Q"),
        color=alt.Color(
            "Categoria:N",
            scale=alt.Scale(range=ui.PALETTE),
            legend=alt.Legend(orient="bottom", columns=3, title=None),
        ),
        tooltip=[
            alt.Tooltip("Categoria:N"),
            alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
            alt.Tooltip("Participacao:Q", title="Participação (%)", format=".1f"),
        ],
    )
    ui.render(donut, height=330)

# ---------------------------------------------------------------------------
# Top produtos + ritmo semanal
# ---------------------------------------------------------------------------
col_a, col_b = st.columns([3, 2], gap="large")

with col_a:
    ui.section("🏆 Top 10 produtos por faturamento")
    top10 = (
        df.groupby("Produto", as_index=False)["Subtotal"].sum()
        .nlargest(10, "Subtotal")
    )
    top10["Participacao"] = top10["Subtotal"] / df["Subtotal"].sum() * 100

    barras_top = alt.Chart(top10).mark_bar(cornerRadiusEnd=6).encode(
        x=alt.X("Subtotal:Q", title="Faturamento (R$)"),
        y=alt.Y("Produto:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
        color=alt.Color("Subtotal:Q", scale=alt.Scale(range=["#C9B8F2", PRIMARY]), legend=None),
        tooltip=[
            alt.Tooltip("Produto:N"),
            alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
            alt.Tooltip("Participacao:Q", title="% do total", format=".1f"),
        ],
    )
    ui.render(barras_top, height=340)

with col_b:
    ui.section("📅 Faturamento por dia da semana")
    dia = df.groupby("Dia_Semana_PT", as_index=False)["Subtotal"].sum()

    barras_dia = alt.Chart(dia).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X("Dia_Semana_PT:N", sort=ORDEM_DIAS, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Subtotal:Q", title="Faturamento (R$)"),
        color=alt.Color("Subtotal:Q", scale=alt.Scale(range=["#BFEAE6", TEAL]), legend=None),
        tooltip=[
            alt.Tooltip("Dia_Semana_PT:N", title="Dia"),
            alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
        ],
    )
    ui.render(barras_dia, height=340)

# ---------------------------------------------------------------------------
# Insights automáticos
# ---------------------------------------------------------------------------
ui.section("💡 Leitura executiva", "Insights calculados automaticamente a partir do recorte atual")
insights = insights_executivos(df)
cols = st.columns(2, gap="medium")
for i, ins in enumerate(insights):
    with cols[i % 2]:
        accent = SECONDARY if ins["tone"] == "warn" else PRIMARY
        ui.insight_card(ins["title"], ins["text"], accent=accent)

ui.footer()
