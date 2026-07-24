"""Temporalidade — padrões de venda por mês, semana, dia e hora."""

import altair as alt
import pandas as pd
import streamlit as st

from core import ui
from core.data import ORDEM_DIAS, ORDEM_PERIODOS, load_data, periodo_dados, sidebar_filters
from core.ui import ACCENT, PRIMARY, SECONDARY, TEAL, fmt_brl, fmt_pct

st.set_page_config(page_title="DKidsFantasias · Temporalidade", page_icon="⏱️", layout="wide")
ui.inject_css()

base = load_data()
df = sidebar_filters(base)

ui.hero(
    "Temporalidade das Vendas",
    f"Quando o dinheiro entra: sazonalidade, dias e horários de pico · {periodo_dados(base)}",
)

if df.empty:
    st.warning("Nenhum dado no recorte selecionado. Ajuste os filtros na barra lateral.")
    st.stop()

# ---------------------------------------------------------------------------
# KPIs temporais
# ---------------------------------------------------------------------------
diario = df.groupby(df["Data_Hora"].dt.normalize())["Subtotal"].sum()
dia_top = df.groupby("Dia_Semana_PT")["Subtotal"].sum().idxmax()
hora_top = int(df.groupby("Hora_do_Dia")["Subtotal"].sum().idxmax())
melhor_dia = diario.idxmax()

ui.kpi_row([
    {"label": "Média por dia de venda", "value": fmt_brl(diario.mean()), "accent": PRIMARY},
    {"label": "Melhor dia registrado", "value": melhor_dia.strftime("%d/%m/%Y"),
     "delta": fmt_brl(diario.max()), "direction": "up", "accent": SECONDARY},
    {"label": "Dia da semana mais forte", "value": dia_top, "accent": ACCENT},
    {"label": "Horário de pico", "value": f"{hora_top}h – {hora_top + 1}h", "accent": TEAL},
])

# ---------------------------------------------------------------------------
# Evolução mensal com variação
# ---------------------------------------------------------------------------
ui.section("📈 Evolução mensal", "Faturamento por mês e variação percentual sobre o mês anterior")

mensal = df.groupby("Ano_Mes", as_index=False)["Subtotal"].sum().sort_values("Ano_Mes")
mensal["Variacao"] = mensal["Subtotal"].pct_change() * 100

area = alt.Chart(mensal).mark_area(
    interpolate="monotone",
    line={"color": PRIMARY, "strokeWidth": 3},
    color=alt.Gradient(
        gradient="linear",
        stops=[alt.GradientStop(color="#FBFBFE", offset=0), alt.GradientStop(color="#C9B8F2", offset=1)],
        x1=1, x2=1, y1=1, y2=0,
    ),
).encode(
    x=alt.X("yearmonth(Ano_Mes):T", title=None, axis=alt.Axis(format="%b/%y", labelAngle=0)),
    y=alt.Y("Subtotal:Q", title="Faturamento (R$)"),
    tooltip=[
        alt.Tooltip("yearmonth(Ano_Mes):T", title="Mês", format="%B/%Y"),
        alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
        alt.Tooltip("Variacao:Q", title="Variação (%)", format="+.1f"),
    ],
)
pontos = alt.Chart(mensal).mark_circle(color=PRIMARY, size=90).encode(
    x="yearmonth(Ano_Mes):T", y="Subtotal:Q",
    tooltip=[
        alt.Tooltip("yearmonth(Ano_Mes):T", title="Mês", format="%B/%Y"),
        alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
        alt.Tooltip("Variacao:Q", title="Variação (%)", format="+.1f"),
    ],
)
rotulos = alt.Chart(mensal).mark_text(dy=-14, fontWeight="bold", color="#3A3752").encode(
    x="yearmonth(Ano_Mes):T", y="Subtotal:Q",
    text=alt.Text("Subtotal:Q", format=",.0f"),
)
ui.render(area + pontos + rotulos, height=340)

if mensal["Variacao"].notna().any():
    ult = mensal.dropna(subset=["Variacao"]).iloc[-1]
    tendencia = "cresceu" if ult["Variacao"] >= 0 else "caiu"
    ui.insight_card(
        "📌 Leitura",
        f"No último mês do recorte o faturamento <b>{tendencia} {fmt_pct(abs(ult['Variacao']))}</b> "
        f"em relação ao mês anterior, somando {fmt_brl(ult['Subtotal'])}. Para uma loja de fantasias, "
        "antecipe estoque para os picos sazonais (festa junina, Halloween, Natal e Carnaval).",
        accent=PRIMARY,
    )

# ---------------------------------------------------------------------------
# Heatmap dia da semana × hora
# ---------------------------------------------------------------------------
ui.section(
    "🔥 Mapa de calor — Dia da semana × Hora",
    "Onde o faturamento se concentra: use para escalar equipe e horário de funcionamento",
)

heat = (
    df.groupby(["Dia_Semana_PT", "Hora_do_Dia"], as_index=False)["Subtotal"]
    .sum()
    .rename(columns={"Subtotal": "Faturamento"})
)
heatmap = alt.Chart(heat).mark_rect(cornerRadius=3).encode(
    x=alt.X("Hora_do_Dia:O", title="Hora do dia", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("Dia_Semana_PT:N", sort=ORDEM_DIAS, title=None),
    color=alt.Color(
        "Faturamento:Q",
        scale=alt.Scale(range=["#F3F1FA", "#9D4EDD", SECONDARY]),
        legend=alt.Legend(title="R$", format=",.0f"),
    ),
    tooltip=[
        alt.Tooltip("Dia_Semana_PT:N", title="Dia"),
        alt.Tooltip("Hora_do_Dia:O", title="Hora"),
        alt.Tooltip("Faturamento:Q", title="Faturamento (R$)", format=",.2f"),
    ],
)
ui.render(heatmap, height=300)

# ---------------------------------------------------------------------------
# Período do dia + semana do ano
# ---------------------------------------------------------------------------
c1, c2 = st.columns([1, 2], gap="large")

with c1:
    ui.section("🌅 Período do dia")
    per = df.groupby("Periodo_do_Dia", as_index=False)["Subtotal"].sum()
    donut_per = alt.Chart(per).mark_arc(innerRadius=55, cornerRadius=4, padAngle=0.02).encode(
        theta=alt.Theta("Subtotal:Q"),
        color=alt.Color(
            "Periodo_do_Dia:N",
            sort=ORDEM_PERIODOS,
            scale=alt.Scale(domain=ORDEM_PERIODOS, range=[ACCENT, PRIMARY, "#3A3752"]),
            legend=alt.Legend(orient="bottom", title=None),
        ),
        tooltip=[
            alt.Tooltip("Periodo_do_Dia:N", title="Período"),
            alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
        ],
    )
    ui.render(donut_per, height=300)

with c2:
    ui.section("📆 Faturamento semanal", "Semanas do ano — identifica picos e vales de demanda")
    semana = df.groupby("Semana_do_Ano", as_index=False)["Subtotal"].sum()
    barras_sem = alt.Chart(semana).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color=TEAL, opacity=0.85).encode(
        x=alt.X("Semana_do_Ano:O", title="Semana do ano", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Subtotal:Q", title="Faturamento (R$)"),
        tooltip=[
            alt.Tooltip("Semana_do_Ano:O", title="Semana"),
            alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
        ],
    )
    media_sem = alt.Chart(semana).mark_rule(color=SECONDARY, strokeDash=[6, 4], strokeWidth=2).encode(
        y="mean(Subtotal):Q"
    )
    ui.render(barras_sem + media_sem, height=300)

# ---------------------------------------------------------------------------
# Top dias
# ---------------------------------------------------------------------------
ui.section("🏆 Os 10 melhores dias do período")

top_dias = (
    diario.nlargest(10)
    .reset_index()
    .rename(columns={"Data_Hora": "Data", "Subtotal": "Faturamento"})
)
top_dias["Dia da semana"] = top_dias["Data"].dt.day_name().map({
    "Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta", "Thursday": "Quinta",
    "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo",
})
top_dias["Data"] = top_dias["Data"].dt.strftime("%d/%m/%Y")

st.dataframe(
    top_dias[["Data", "Dia da semana", "Faturamento"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Faturamento": st.column_config.NumberColumn("Faturamento (R$)", format="R$ %.2f"),
    },
)

ui.footer()
