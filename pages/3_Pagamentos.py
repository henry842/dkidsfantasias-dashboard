"""Pagamentos — mix de recebimento, ticket por forma e evolução do share."""

import altair as alt
import streamlit as st

from core import ui
from core.data import load_data, periodo_dados, sidebar_filters
from core.ui import ACCENT, PRIMARY, SECONDARY, TEAL, fmt_brl, fmt_int, fmt_pct

st.set_page_config(page_title="DKidsFantasias · Pagamentos", page_icon="💳", layout="wide")
ui.inject_css()

base = load_data()
df = sidebar_filters(base)

ui.hero(
    "Análise de Pagamentos",
    f"Como o cliente paga: mix de recebimento, ticket e evolução · {periodo_dados(base)}",
)

if df.empty:
    st.warning("Nenhum dado no recorte selecionado. Ajuste os filtros na barra lateral.")
    st.stop()

total = df["Subtotal"].sum()
CORES_PAG = {"Cartão": PRIMARY, "Pix": TEAL, "Dinheiro": ACCENT}

# ---------------------------------------------------------------------------
# Agregações principais
# ---------------------------------------------------------------------------
pag = (
    df.groupby("Forma_de_Pagamento_Simples", as_index=False)
    .agg(
        Faturamento=("Subtotal", "sum"),
        Vendas=("Codigo_da_Venda", "nunique"),
    )
    .sort_values("Faturamento", ascending=False)
)
pag["Participacao"] = pag["Faturamento"] / total * 100
pag["Ticket"] = pag["Faturamento"] / pag["Vendas"]

lider = pag.iloc[0]
maior_ticket = pag.nlargest(1, "Ticket").iloc[0]

ui.kpi_row([
    {"label": "Forma líder", "value": str(lider["Forma_de_Pagamento_Simples"]),
     "delta": f"{fmt_pct(lider['Participacao'])} do faturamento", "direction": "up", "accent": PRIMARY},
    {"label": "Maior ticket médio", "value": str(maior_ticket["Forma_de_Pagamento_Simples"]),
     "delta": fmt_brl(maior_ticket["Ticket"]), "direction": "up", "accent": ACCENT},
    {"label": "Formas ativas", "value": fmt_int(len(pag)), "accent": TEAL},
    {"label": "Vendas no recorte", "value": fmt_int(pag["Vendas"].sum()), "accent": SECONDARY},
])

# ---------------------------------------------------------------------------
# Mix + ticket por forma
# ---------------------------------------------------------------------------
c1, c2 = st.columns(2, gap="large")

dominio = pag["Forma_de_Pagamento_Simples"].tolist()
cores = [CORES_PAG.get(f, SECONDARY) for f in dominio]

with c1:
    ui.section("🧩 Mix de recebimento", "Participação de cada forma no faturamento")
    donut = alt.Chart(pag).mark_arc(innerRadius=70, cornerRadius=4, padAngle=0.02).encode(
        theta=alt.Theta("Faturamento:Q"),
        color=alt.Color(
            "Forma_de_Pagamento_Simples:N",
            scale=alt.Scale(domain=dominio, range=cores),
            legend=alt.Legend(orient="bottom", title=None),
        ),
        tooltip=[
            alt.Tooltip("Forma_de_Pagamento_Simples:N", title="Forma"),
            alt.Tooltip("Faturamento:Q", title="Faturamento (R$)", format=",.2f"),
            alt.Tooltip("Participacao:Q", title="Participação (%)", format=".1f"),
            alt.Tooltip("Vendas:Q", title="Nº vendas"),
        ],
    )
    ui.render(donut, height=320)

with c2:
    ui.section("🎟️ Ticket médio por forma", "Valor médio por venda em cada meio de pagamento")
    barras_tkt = alt.Chart(pag).mark_bar(cornerRadiusEnd=6, size=38).encode(
        x=alt.X("Ticket:Q", title="Ticket médio (R$)"),
        y=alt.Y("Forma_de_Pagamento_Simples:N", sort="-x", title=None),
        color=alt.Color(
            "Forma_de_Pagamento_Simples:N",
            scale=alt.Scale(domain=dominio, range=cores),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("Forma_de_Pagamento_Simples:N", title="Forma"),
            alt.Tooltip("Ticket:Q", title="Ticket médio (R$)", format=",.2f"),
            alt.Tooltip("Vendas:Q", title="Nº vendas"),
        ],
    )
    rotulo = alt.Chart(pag).mark_text(align="left", dx=6, fontWeight="bold", color="#3A3752").encode(
        x="Ticket:Q",
        y=alt.Y("Forma_de_Pagamento_Simples:N", sort="-x"),
        text=alt.Text("Ticket:Q", format=",.2f"),
    )
    ui.render(barras_tkt + rotulo, height=320)

# ---------------------------------------------------------------------------
# Evolução do share mês a mês
# ---------------------------------------------------------------------------
ui.section(
    "📈 Evolução do mix mês a mês",
    "Participação percentual de cada forma no faturamento mensal — mudanças de comportamento do cliente",
)

evolucao = (
    df.groupby(["Ano_Mes", "Forma_de_Pagamento_Simples"], as_index=False)["Subtotal"].sum()
)
stacked = alt.Chart(evolucao).mark_area(interpolate="monotone", opacity=0.9).encode(
    x=alt.X("yearmonth(Ano_Mes):T", title=None, axis=alt.Axis(format="%b/%y", labelAngle=0)),
    y=alt.Y("Subtotal:Q", stack="normalize", title="Participação", axis=alt.Axis(format=".0%")),
    color=alt.Color(
        "Forma_de_Pagamento_Simples:N",
        scale=alt.Scale(domain=dominio, range=cores),
        legend=alt.Legend(orient="bottom", title=None),
    ),
    tooltip=[
        alt.Tooltip("yearmonth(Ano_Mes):T", title="Mês", format="%B/%Y"),
        alt.Tooltip("Forma_de_Pagamento_Simples:N", title="Forma"),
        alt.Tooltip("Subtotal:Q", title="Faturamento (R$)", format=",.2f"),
    ],
)
ui.render(stacked, height=320)

# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------
ui.section("💡 Leitura executiva")

pix_pct = float(pag.loc[pag["Forma_de_Pagamento_Simples"] == "Pix", "Participacao"].sum())
dinheiro_pct = float(pag.loc[pag["Forma_de_Pagamento_Simples"] == "Dinheiro", "Participacao"].sum())

c3, c4 = st.columns(2, gap="medium")
with c3:
    ui.insight_card(
        "💳 Custo de recebimento",
        f"<b>{lider['Forma_de_Pagamento_Simples']}</b> concentra {fmt_pct(lider['Participacao'])} do faturamento "
        f"({fmt_brl(lider['Faturamento'])}). Se for cartão, vale negociar a taxa da maquininha — "
        "cada 0,5% de redução vai direto para a margem.",
        accent=PRIMARY,
    )
    ui.insight_card(
        "⚡ Pix como aliado do caixa",
        f"O Pix responde por {fmt_pct(pix_pct)} das vendas: recebimento instantâneo e sem taxas. "
        "Incentivar o Pix com pequenos benefícios melhora o fluxo de caixa.",
        accent=TEAL,
    )
with c4:
    ui.insight_card(
        "🎟️ Ticket revela comportamento",
        f"O maior ticket médio está em <b>{maior_ticket['Forma_de_Pagamento_Simples']}</b> "
        f"({fmt_brl(maior_ticket['Ticket'])}) — compras maiores tendem a usar esse meio. "
        "Use parcelamento como alavanca em itens de maior valor.",
        accent=ACCENT,
    )
    ui.insight_card(
        "💵 Gestão do dinheiro físico",
        f"Dinheiro em espécie representa {fmt_pct(dinheiro_pct)} do faturamento. "
        "Mantenha rotina de sangria e conferência de caixa para reduzir risco operacional.",
        accent=SECONDARY,
    )

ui.footer()
