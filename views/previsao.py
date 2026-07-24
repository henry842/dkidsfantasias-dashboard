"""Previsão de Faturamento — XGBoost com validação honesta e projeção de 30 dias."""

import altair as alt
import pandas as pd
import streamlit as st

from core import ui
from core.data import load_data, periodo_dados
from core.forecast import prever_faturamento
from core.ui import ACCENT, PRIMARY, SECONDARY, TEAL, fmt_brl, fmt_pct

ui.inject_css()

base = load_data()

ui.hero(
    "Previsão de Faturamento",
    f"Projeção dos próximos dias de venda com XGBoost · Histórico: {periodo_dados(base)}",
)

st.sidebar.markdown("## 🎛️ Parâmetros")
horizonte = st.sidebar.slider("Dias de venda a projetar", 7, 60, 30, step=1)
st.sidebar.caption(
    "A previsão usa sempre a base completa (sem filtros) — "
    "o modelo precisa do histórico contínuo para aprender a sazonalidade."
)


@st.cache_data(show_spinner="Treinando modelo de previsão...")
def _rodar_previsao(horizonte: int) -> dict:
    return prever_faturamento(load_data(), horizonte=horizonte)


try:
    resultado = _rodar_previsao(horizonte)
except ValueError as e:
    st.warning(str(e))
    st.stop()

hist = resultado["historico"]
futuro = resultado["futuro"]
m = resultado["metricas"]

# ---------------------------------------------------------------------------
# Métricas de confiabilidade
# ---------------------------------------------------------------------------
ui.kpi_row([
    {"label": f"Projeção · próx. {horizonte} dias de venda", "value": fmt_brl(m["total_previsto"]),
     "accent": PRIMARY},
    {"label": "Erro médio diário (MAE)", "value": fmt_brl(m["mae"]),
     "delta": f"validado em {m['holdout_dias']} dias fora do treino", "direction": "neutral", "accent": ACCENT},
    {"label": "Erro relativo (WMAPE)", "value": fmt_pct(m["wmape"]),
     "delta": "quanto menor, melhor", "direction": "neutral", "accent": TEAL},
    {"label": "Cobertura do intervalo 95%", "value": fmt_pct(m["cobertura"], 0),
     "delta": "dias reais dentro da faixa prevista", "direction": "neutral", "accent": SECONDARY},
])

# ---------------------------------------------------------------------------
# Gráfico principal
# ---------------------------------------------------------------------------
ui.section(
    "📊 Histórico, validação e projeção",
    "Roxo: faturamento real · Rosa tracejado: previsão na validação · Faixa: intervalo de 95% na projeção",
)

hist_plot = hist.copy()
futuro_plot = futuro.copy()

linha_real = alt.Chart(hist_plot).mark_line(color=PRIMARY, strokeWidth=1.8, opacity=0.9).encode(
    x=alt.X("data:T", title=None, axis=alt.Axis(format="%d/%m")),
    y=alt.Y("faturamento:Q", title="Faturamento diário (R$)"),
    tooltip=[
        alt.Tooltip("data:T", title="Data", format="%d/%m/%Y"),
        alt.Tooltip("faturamento:Q", title="Real (R$)", format=",.2f"),
        alt.Tooltip("previsto:Q", title="Previsto (R$)", format=",.2f"),
        alt.Tooltip("conjunto:N", title="Conjunto"),
    ],
)
linha_ajuste = alt.Chart(hist_plot[hist_plot["conjunto"] == "Validação"]).mark_line(
    color=SECONDARY, strokeWidth=2, strokeDash=[5, 3]
).encode(x="data:T", y="previsto:Q")

banda_fut = alt.Chart(futuro_plot).mark_area(color=SECONDARY, opacity=0.15).encode(
    x="data:T",
    y=alt.Y("limite_inferior:Q", title=""),
    y2="limite_superior:Q",
)
linha_fut = alt.Chart(futuro_plot).mark_line(
    color=SECONDARY, strokeWidth=2.5, point=alt.OverlayMarkDef(color=SECONDARY, size=30)
).encode(
    x="data:T",
    y="previsto:Q",
    tooltip=[
        alt.Tooltip("data:T", title="Data", format="%d/%m/%Y"),
        alt.Tooltip("previsto:Q", title="Previsto (R$)", format=",.2f"),
        alt.Tooltip("limite_inferior:Q", title="Mínimo esperado (R$)", format=",.2f"),
        alt.Tooltip("limite_superior:Q", title="Máximo esperado (R$)", format=",.2f"),
    ],
)
corte = alt.Chart(pd.DataFrame({"data": [hist["data"].max()]})).mark_rule(
    color="#A8A4BC", strokeDash=[6, 4]
).encode(x="data:T")

ui.render(banda_fut + linha_real + linha_ajuste + linha_fut + corte, height=400)

ui.insight_card(
    "🧪 Como interpretar a confiabilidade",
    f"O modelo foi avaliado em <b>{m['holdout_dias']} dias que ele nunca viu durante o treino</b>. "
    f"Nesses dias, errou em média {fmt_brl(m['mae'])} por dia ({fmt_pct(m['wmape'])} do faturamento). "
    f"A faixa rosa indica o intervalo em que o faturamento real deve ficar em 95% dos casos — "
    f"na validação, {fmt_pct(m['cobertura'], 0)} dos dias ficaram dentro dela.",
    accent=PRIMARY,
)

# ---------------------------------------------------------------------------
# Projeção semanal + tabela
# ---------------------------------------------------------------------------
c1, c2 = st.columns([2, 3], gap="large")

with c1:
    ui.section("📆 Projeção por semana", "Faturamento previsto agregado por semana")
    fut_sem = futuro.copy()
    fut_sem["Semana"] = fut_sem["data"].dt.to_period("W").dt.start_time
    sem = fut_sem.groupby("Semana", as_index=False).agg(
        Previsto=("previsto", "sum"),
        Minimo=("limite_inferior", "sum"),
        Maximo=("limite_superior", "sum"),
    )
    barras_sem = alt.Chart(sem).mark_bar(
        cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color=PRIMARY, size=40
    ).encode(
        x=alt.X("Semana:T", title="Semana (início)", axis=alt.Axis(format="%d/%m", labelAngle=0)),
        y=alt.Y("Previsto:Q", title="Faturamento previsto (R$)"),
        tooltip=[
            alt.Tooltip("Semana:T", title="Semana de", format="%d/%m/%Y"),
            alt.Tooltip("Previsto:Q", title="Previsto (R$)", format=",.2f"),
            alt.Tooltip("Minimo:Q", title="Cenário conservador (R$)", format=",.2f"),
            alt.Tooltip("Maximo:Q", title="Cenário otimista (R$)", format=",.2f"),
        ],
    )
    erro_sem = alt.Chart(sem).mark_errorbar(color=SECONDARY, ticks=True).encode(
        x="Semana:T",
        y=alt.Y("Minimo:Q", title=""),
        y2="Maximo:Q",
    )
    ui.render(barras_sem + erro_sem, height=320)

with c2:
    ui.section("📋 Detalhe diário da projeção")
    tabela = futuro.copy()
    tabela["Dia da semana"] = tabela["data"].dt.day_name().map({
        "Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta", "Thursday": "Quinta",
        "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo",
    })
    tabela["Data"] = tabela["data"].dt.strftime("%d/%m/%Y")
    tabela = tabela[["Data", "Dia da semana", "previsto", "limite_inferior", "limite_superior"]]
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=320,
        column_config={
            "previsto": st.column_config.NumberColumn("Previsto (R$)", format="R$ %.2f"),
            "limite_inferior": st.column_config.NumberColumn("Mínimo esperado (R$)", format="R$ %.2f"),
            "limite_superior": st.column_config.NumberColumn("Máximo esperado (R$)", format="R$ %.2f"),
        },
    )
    st.download_button(
        "📥 Baixar projeção (CSV)",
        data=tabela.to_csv(index=False).encode("utf-8-sig"),
        file_name="previsao_faturamento_dkids.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Metodologia
# ---------------------------------------------------------------------------
with st.expander("🔬 Metodologia do modelo (para quem quer entender o motor)"):
    st.markdown(f"""
**Modelo:** XGBoost (gradient boosting de árvores de decisão), treinado sobre o faturamento diário.

**Variáveis utilizadas:**
- Calendário: dia da semana, dia do mês, mês, semana do ano, indicador de fim de semana
- Memória recente: faturamento do dia anterior (*lag 1*) e de 7 dias atrás (*lag 7*)
- Tendência: médias móveis de 7 e 28 dias

**Validação honesta:** os últimos **{m['holdout_dias']} dias** da base são separados antes do treino
e usados apenas para medir o erro — o modelo nunca os vê. As métricas exibidas (MAE e WMAPE)
vêm exclusivamente desse período, o que evita a ilusão de precisão de modelos avaliados
nos próprios dados de treino.

**Projeção futura:** o modelo é re-treinado com todo o histórico e projeta um dia por vez,
realimentando as defasagens com as próprias previsões. Dias da semana em que a loja
não registra vendas no histórico são automaticamente excluídos da projeção.

**Intervalo de confiança:** calculado a partir do desvio-padrão dos erros na validação
(± 1,96 desvios ≈ 95% de confiança).

**Limitações:** o modelo aprende padrões do histórico disponível. Eventos inéditos
(promoções novas, feriados atípicos, mudanças de horário) não são antecipados —
use a projeção como referência de planejamento, não como garantia.
""")

ui.footer()
