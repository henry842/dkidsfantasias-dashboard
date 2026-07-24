"""Produtos & Portfólio — Pareto, curva ABC, matriz estratégica e consistência de preço."""

import altair as alt
import pandas as pd
import streamlit as st

from core import ui
from core.data import load_data, periodo_dados, sidebar_filters
from core.ui import ACCENT, PRIMARY, SECONDARY, TEAL, fmt_brl, fmt_int, fmt_pct

ui.inject_css()

base = load_data()
df = sidebar_filters(base)

ui.hero(
    "Produtos & Portfólio",
    f"Concentração de receita, curva ABC e posicionamento estratégico · {periodo_dados(base)}",
)

if df.empty:
    st.warning("Nenhum dado no recorte selecionado. Ajuste os filtros na barra lateral.")
    st.stop()

total = df["Subtotal"].sum()

# ---------------------------------------------------------------------------
# Curva ABC (base para KPIs e gráficos)
# ---------------------------------------------------------------------------
fat_prod = (
    df.groupby("Produto", as_index=False)
    .agg(Faturamento=("Subtotal", "sum"), Quantidade=("Qtd", "sum"))
    .sort_values("Faturamento", ascending=False)
    .reset_index(drop=True)
)
fat_prod["Acumulado_pct"] = fat_prod["Faturamento"].cumsum() / total * 100
fat_prod["Classe"] = pd.cut(
    fat_prod["Acumulado_pct"], bins=[0, 80, 95, 100.001], labels=["A", "B", "C"]
).astype(str)
fat_prod["Rank"] = fat_prod.index + 1

n_a = int((fat_prod["Classe"] == "A").sum())
n_b = int((fat_prod["Classe"] == "B").sum())
n_c = int((fat_prod["Classe"] == "C").sum())
top5_pct = fat_prod.head(5)["Faturamento"].sum() / total * 100

ui.kpi_row([
    {"label": "Produtos no portfólio", "value": fmt_int(len(fat_prod)), "accent": PRIMARY},
    {"label": "Classe A (80% da receita)", "value": f"{n_a} produtos", "accent": SECONDARY},
    {"label": "Classe B (15% seguintes)", "value": f"{n_b} produtos", "accent": ACCENT},
    {"label": "Classe C (cauda longa)", "value": f"{n_c} produtos", "accent": TEAL},
    {"label": "Top 5 concentram", "value": fmt_pct(top5_pct), "accent": "#4CC9F0"},
])

# ---------------------------------------------------------------------------
# Pareto
# ---------------------------------------------------------------------------
ui.section(
    "📊 Curva ABC — Pareto dos 30 principais produtos",
    "Barras: faturamento individual · Linha: participação acumulada · Faixa: limite de 80%",
)

pareto = fat_prod.head(30)
base_chart = alt.Chart(pareto).encode(
    x=alt.X("Rank:O", title="Ranking do produto", axis=alt.Axis(labelAngle=0))
)
barras = base_chart.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    y=alt.Y("Faturamento:Q", title="Faturamento (R$)"),
    color=alt.Color(
        "Classe:N",
        scale=alt.Scale(domain=["A", "B", "C"], range=[PRIMARY, ACCENT, "#C9C5DB"]),
        legend=alt.Legend(title="Classe ABC", orient="top-right"),
    ),
    tooltip=[
        alt.Tooltip("Produto:N"),
        alt.Tooltip("Faturamento:Q", title="Faturamento (R$)", format=",.2f"),
        alt.Tooltip("Acumulado_pct:Q", title="Acumulado (%)", format=".1f"),
        alt.Tooltip("Classe:N"),
    ],
)
linha_acum = base_chart.mark_line(
    color=SECONDARY, strokeWidth=2.5, point=alt.OverlayMarkDef(color=SECONDARY, size=45)
).encode(
    y=alt.Y("Acumulado_pct:Q", title="Acumulado (%)", axis=alt.Axis(orient="right"), scale=alt.Scale(domain=[0, 100])),
)
regra_80 = alt.Chart(pd.DataFrame({"y": [80]})).mark_rule(color=SECONDARY, strokeDash=[6, 4], opacity=0.6).encode(
    y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[0, 100]))
)
ui.render(alt.layer(barras, linha_acum + regra_80).resolve_scale(y="independent"), height=360)

ui.insight_card(
    "🎯 Leitura",
    f"<b>{n_a} produtos (Classe A)</b> sustentam 80% do faturamento — merecem prioridade absoluta em "
    f"estoque, exposição e reposição. Os <b>{n_c} produtos da Classe C</b> respondem por apenas 5% da "
    "receita: avalie enxugar o portfólio ou usá-los como itens de complemento de ticket.",
    accent=SECONDARY,
)

# ---------------------------------------------------------------------------
# Matriz estratégica
# ---------------------------------------------------------------------------
ui.section(
    "🧭 Matriz estratégica — Volume × Ticket",
    "Cada ponto é um produto. Linhas tracejadas: medianas. Tamanho: faturamento total.",
)

mapa = (
    df.groupby("Produto", as_index=False)
    .agg(
        Volume=("Qtd", "sum"),
        Ticket_Medio=("Valor_Unit", "mean"),
        Faturamento=("Subtotal", "sum"),
        Categoria=("Categoria", "first"),
    )
)
vol_med = mapa["Volume"].median()
tkt_med = mapa["Ticket_Medio"].median()


def _quadrante(r):
    if r["Volume"] >= vol_med and r["Ticket_Medio"] >= tkt_med:
        return "⭐ Estrela (alto volume, alto ticket)"
    if r["Volume"] >= vol_med:
        return "📦 Fluxo (alto volume, baixo ticket)"
    if r["Ticket_Medio"] >= tkt_med:
        return "💎 Premium (baixo volume, alto ticket)"
    return "⚠️ Baixo impacto"


mapa["Perfil"] = mapa.apply(_quadrante, axis=1)

scatter = alt.Chart(mapa).mark_circle(opacity=0.75).encode(
    x=alt.X("Volume:Q", title="Volume vendido (unidades)", scale=alt.Scale(type="sqrt")),
    y=alt.Y("Ticket_Medio:Q", title="Preço médio (R$)", scale=alt.Scale(type="sqrt")),
    size=alt.Size("Faturamento:Q", scale=alt.Scale(range=[40, 700]), legend=None),
    color=alt.Color(
        "Perfil:N",
        scale=alt.Scale(
            domain=[
                "⭐ Estrela (alto volume, alto ticket)",
                "📦 Fluxo (alto volume, baixo ticket)",
                "💎 Premium (baixo volume, alto ticket)",
                "⚠️ Baixo impacto",
            ],
            range=[PRIMARY, TEAL, ACCENT, "#C9C5DB"],
        ),
        legend=alt.Legend(title=None, orient="bottom", columns=2),
    ),
    tooltip=[
        alt.Tooltip("Produto:N"),
        alt.Tooltip("Perfil:N"),
        alt.Tooltip("Volume:Q", title="Unidades"),
        alt.Tooltip("Ticket_Medio:Q", title="Preço médio (R$)", format=",.2f"),
        alt.Tooltip("Faturamento:Q", title="Faturamento (R$)", format=",.2f"),
    ],
)
regua_v = alt.Chart(pd.DataFrame({"x": [vol_med]})).mark_rule(strokeDash=[5, 5], color="#A8A4BC").encode(x="x:Q")
regua_h = alt.Chart(pd.DataFrame({"y": [tkt_med]})).mark_rule(strokeDash=[5, 5], color="#A8A4BC").encode(y="y:Q")
ui.render(scatter + regua_v + regua_h, height=420)

c1, c2 = st.columns(2, gap="medium")
with c1:
    estrelas = mapa[mapa["Perfil"].str.startswith("⭐")].nlargest(5, "Faturamento")["Produto"].tolist()
    if estrelas:
        ui.insight_card(
            "⭐ Estrelas do portfólio",
            "Produtos que combinam giro e valor: <b>" + "</b>, <b>".join(estrelas[:3]) + "</b>. "
            "Nunca deixe faltar em estoque — cada ruptura aqui custa caro.",
            accent=PRIMARY,
        )
with c2:
    premium = mapa[mapa["Perfil"].str.startswith("💎")].nlargest(3, "Ticket_Medio")["Produto"].tolist()
    if premium:
        ui.insight_card(
            "💎 Âncoras premium",
            "Itens de alto valor como <b>" + "</b>, <b>".join(premium[:2]) + "</b> elevam a percepção da loja "
            "e funcionam como âncora de preço em vitrines e combos.",
            accent=ACCENT,
        )

# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
ui.section("🗂️ Performance por categoria")

cat = (
    df.groupby("Categoria", as_index=False)
    .agg(
        Faturamento=("Subtotal", "sum"),
        Unidades=("Qtd", "sum"),
        Preco_Medio=("Valor_Unit", "mean"),
        Produtos=("Produto", "nunique"),
    )
    .sort_values("Faturamento", ascending=False)
)
cat["Participacao"] = cat["Faturamento"] / total * 100

st.dataframe(
    cat,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Categoria": st.column_config.TextColumn("Categoria"),
        "Faturamento": st.column_config.NumberColumn("Faturamento (R$)", format="R$ %.2f"),
        "Unidades": st.column_config.NumberColumn("Unidades", format="%d"),
        "Preco_Medio": st.column_config.NumberColumn("Preço médio (R$)", format="R$ %.2f"),
        "Produtos": st.column_config.NumberColumn("Nº produtos", format="%d"),
        "Participacao": st.column_config.ProgressColumn("Participação", format="%.1f%%", min_value=0, max_value=100),
    },
)

# ---------------------------------------------------------------------------
# Consistência de preço
# ---------------------------------------------------------------------------
ui.section(
    "💸 Consistência de preço",
    "Produtos vendidos com maior variação de preço unitário — possíveis descontos não padronizados ou erros de cadastro",
)

preco = (
    df.groupby("Produto")
    .agg(
        Preco_Medio=("Valor_Unit", "mean"),
        Preco_Min=("Valor_Unit", "min"),
        Preco_Max=("Valor_Unit", "max"),
        Desvio=("Valor_Unit", "std"),
        Vendas=("Codigo_da_Venda", "nunique"),
    )
    .dropna(subset=["Desvio"])
)
preco = preco[preco["Vendas"] >= 3]
preco["Coef_Variacao"] = preco["Desvio"] / preco["Preco_Medio"] * 100
suspeitos = preco.nlargest(8, "Coef_Variacao").reset_index()

if suspeitos.empty:
    st.success("Nenhuma variação de preço relevante encontrada no recorte atual.")
else:
    st.dataframe(
        suspeitos[["Produto", "Vendas", "Preco_Min", "Preco_Medio", "Preco_Max", "Coef_Variacao"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Vendas": st.column_config.NumberColumn("Nº vendas", format="%d"),
            "Preco_Min": st.column_config.NumberColumn("Mínimo (R$)", format="R$ %.2f"),
            "Preco_Medio": st.column_config.NumberColumn("Médio (R$)", format="R$ %.2f"),
            "Preco_Max": st.column_config.NumberColumn("Máximo (R$)", format="R$ %.2f"),
            "Coef_Variacao": st.column_config.ProgressColumn(
                "Variação", format="%.0f%%", min_value=0, max_value=float(suspeitos["Coef_Variacao"].max())
            ),
        },
    )
    pior = suspeitos.iloc[0]
    ui.insight_card(
        "⚠️ Ponto de atenção",
        f"<b>{pior['Produto']}</b> foi vendido entre {fmt_brl(pior['Preco_Min'])} e {fmt_brl(pior['Preco_Max'])}. "
        "Padronize a política de descontos ou revise o cadastro para proteger a margem.",
        accent=SECONDARY,
    )

ui.footer()
