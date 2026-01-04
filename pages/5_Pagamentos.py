import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Pagamentos", layout="wide")

# ===============================
# 0. Checagem do DataFrame
# ===============================
if "df" not in st.session_state:
    st.error("❌ DataFrame não carregado. Volte para a página inicial.")
    st.stop()

df = st.session_state.df.copy()

if df.empty:
    st.warning("Nenhum dado disponível.")
    st.stop()

# ===============================
# 1. Pré-processamento
# ===============================
# Garantir datetime
df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], errors='coerce')

# Garantir que os valores de pagamento sejam numéricos
df['Subtotal_Verificado'] = pd.to_numeric(df['Subtotal_Verificado'], errors='coerce')
df['Qtd'] = pd.to_numeric(df['Qtd'], errors='coerce')
df['Ticket'] = pd.to_numeric(df['Ticket'], errors='coerce')

# Colunas de pagamento
df['Forma_de_Pagamento'] = df['Forma_de_Pagamento'].astype(str)
df['Forma_de_Pagamento_Simples'] = df['Forma_de_Pagamento_Simples'].astype(str)

# ===============================
# 2. Filtros Interativos
# ===============================
st.title("💳 Análise Estratégica de Pagamentos")
st.caption("KPIs e insights sobre formas de pagamento")

# Filtros de selectbox
vendedor_select = st.selectbox("Filtrar por Vendedor", ["Todos"] + list(df['Vendedor'].unique()))
categoria_select = st.selectbox("Filtrar por Categoria", ["Todos"] + list(df['Categoria'].unique()))
data_inicio = st.date_input("Data Início", value=df["Data_Hora"].min().date())
data_fim = st.date_input("Data Fim", value=df["Data_Hora"].max().date())

# Filtros de multiselect
vendedores = st.multiselect("Selecione os Vendedores", df["Vendedor"].unique(), default=df["Vendedor"].unique())
categorias = st.multiselect("Selecione as Categorias", df["Categoria"].unique(), default=df["Categoria"].unique())

# Filtragem combinada
df_filtrado = df.copy()
if vendedor_select != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Vendedor'] == vendedor_select]
if categoria_select != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria_select]

df_filtrado = df_filtrado[df_filtrado["Vendedor"].isin(vendedores)]
df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(categorias)]

# Filtrar por datas normalizadas
df_filtrado = df_filtrado[
    (df_filtrado["Data_Hora"].dt.normalize() >= pd.to_datetime(data_inicio)) &
    (df_filtrado["Data_Hora"].dt.normalize() <= pd.to_datetime(data_fim))
]

# ===============================
# 3. KPIs Executivos
# ===============================
faturamento_total = df_filtrado['Subtotal_Verificado'].sum()
total_itens = int(df_filtrado['Qtd'].sum())
ticket_medio = df_filtrado['Ticket'].mean() if not df_filtrado.empty else 0

col1, col2, col3 = st.columns(3)
col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}")
col2.metric("📦 Total de Itens Vendidos", total_itens)
col3.metric("🎟️ Ticket Médio", f"R$ {ticket_medio:,.2f}")

st.divider()

# ===============================
# 4. Faturamento por Forma de Pagamento
# ===============================
st.subheader("📊 Faturamento por Forma de Pagamento")
pagamentos = (
    df_filtrado.groupby("Forma_de_Pagamento_Simples")["Subtotal_Verificado"]
    .sum()
    .reset_index()
    .sort_values("Subtotal_Verificado", ascending=False)
)

chart_pagamento = alt.Chart(pagamentos).mark_bar().encode(
    x=alt.X("Forma_de_Pagamento_Simples:N", sort="-y", title="Forma de Pagamento"),
    y=alt.Y("Subtotal_Verificado:Q", title="Faturamento"),
    color=alt.Color("Subtotal_Verificado:Q", scale=alt.Scale(scheme="greens")),
    tooltip=["Forma_de_Pagamento_Simples", "Subtotal_Verificado"]
)
st.altair_chart(chart_pagamento, use_container_width=True)

# ===============================
# 5. Frequência de Uso das Formas de Pagamento
# ===============================
st.subheader("📈 Frequência de Uso")
freq_pagamento = (
    df_filtrado.groupby("Forma_de_Pagamento_Simples")["Codigo_da_Venda"]
    .nunique()
    .reset_index()
    .rename(columns={"Codigo_da_Venda": "Qtd_Vendas"})
    .sort_values("Qtd_Vendas", ascending=False)
)

chart_freq = alt.Chart(freq_pagamento).mark_bar().encode(
    x=alt.X("Forma_de_Pagamento_Simples:N", sort="-y", title="Forma de Pagamento"),
    y=alt.Y("Qtd_Vendas:Q", title="Número de Vendas"),
    color=alt.Color("Qtd_Vendas:Q", scale=alt.Scale(scheme="blues")),
    tooltip=["Forma_de_Pagamento_Simples", "Qtd_Vendas"]
)
st.altair_chart(chart_freq, use_container_width=True)

# ===============================
# 6. Ticket Médio por Forma de Pagamento
# ===============================
st.subheader("🎟️ Ticket Médio por Forma de Pagamento")
ticket_pagamento = (
    df_filtrado.groupby("Forma_de_Pagamento_Simples")["Ticket"]
    .mean()
    .reset_index()
    .sort_values("Ticket", ascending=False)
)

chart_ticket = alt.Chart(ticket_pagamento).mark_bar().encode(
    x=alt.X("Forma_de_Pagamento_Simples:N", sort="-y", title="Forma de Pagamento"),
    y=alt.Y("Ticket:Q", title="Ticket Médio"),
    color=alt.Color("Ticket:Q", scale=alt.Scale(scheme="oranges")),
    tooltip=["Forma_de_Pagamento_Simples", "Ticket"]
)
st.altair_chart(chart_ticket, use_container_width=True)

# ===============================
# 7. Insights Estratégicos Automáticos
# ===============================
st.subheader("📌 Insights Executivos")

top_forma = pagamentos.iloc[0]["Forma_de_Pagamento_Simples"]
top_valor = pagamentos.iloc[0]["Subtotal_Verificado"]

most_freq = freq_pagamento.iloc[0]["Forma_de_Pagamento_Simples"]
most_freq_val = freq_pagamento.iloc[0]["Qtd_Vendas"]

highest_ticket = ticket_pagamento.iloc[0]["Forma_de_Pagamento_Simples"]
highest_ticket_val = ticket_pagamento.iloc[0]["Ticket"]

st.success(
    f"- 💰 Forma de pagamento que mais faturou: **{top_forma}** → R$ {top_valor:,.2f}\n"
    f"- 📈 Forma mais usada: **{most_freq}** → {most_freq_val} vendas\n"
    f"- 🎟️ Forma com maior ticket médio: **{highest_ticket}** → R$ {highest_ticket_val:,.2f}\n"
    "- ⚠️ Use esses dados para priorizar conciliação e promoções estratégicas."
)

# ===============================
# 8. Faturamento por Dia da Semana
# ===============================
st.subheader("📅 Faturamento por Dia da Semana")
faturamento_dia_semana = (
    df_filtrado.groupby(df_filtrado["Data_Hora"].dt.day_name())["Subtotal_Verificado"]
    .sum()
    .reset_index()
    .sort_values("Subtotal_Verificado", ascending=False)
)

chart_dia_semana = alt.Chart(faturamento_dia_semana).mark_bar().encode(
    x=alt.X("Data_Hora:N", sort="-y", title="Dia da Semana"),
    y=alt.Y("Subtotal_Verificado:Q", title="Faturamento"),
    color=alt.Color("Subtotal_Verificado:Q", scale=alt.Scale(scheme="blues")),
    tooltip=[alt.Tooltip("Data_Hora", title="Dia"), alt.Tooltip("Subtotal_Verificado", title="Faturamento")]
)
st.altair_chart(chart_dia_semana, use_container_width=True)

# ===============================
# 9. Evolução do Faturamento (Linha/Tempo Melhorada)
# ===============================
st.subheader("📈 Evolução do Faturamento")

# Agrupar por mês
faturamento_tempo = (
    df_filtrado.groupby(df_filtrado["Data_Hora"].dt.to_period("M"))["Subtotal_Verificado"]
    .sum()
    .reset_index()
)
faturamento_tempo["Data_Hora"] = faturamento_tempo["Data_Hora"].dt.to_timestamp()

# Calcular variação mês a mês
faturamento_tempo["Variacao"] = faturamento_tempo["Subtotal_Verificado"].pct_change().fillna(0) * 100

# Linha principal
linha = alt.Chart(faturamento_tempo).mark_line(interpolate='monotone', strokeWidth=3, color="#1f77b4").encode(
    x=alt.X("Data_Hora:T", title="Mês", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
    y=alt.Y("Subtotal_Verificado:Q", title="Faturamento (R$)"),
    tooltip=[
        alt.Tooltip("Data_Hora:T", title="Mês", format="%B %Y"),
        alt.Tooltip("Subtotal_Verificado:Q", title="Faturamento", format=",.2f"),
        alt.Tooltip("Variacao:Q", title="Variação", format=".2f")
    ]
)

# Área sombreada
area = alt.Chart(faturamento_tempo).mark_area(opacity=0.2, interpolate='monotone', color="#1f77b4").encode(
    x="Data_Hora:T",
    y="Subtotal_Verificado:Q"
)

# Pontos proporcionais ao faturamento
pontos = alt.Chart(faturamento_tempo).mark_circle(size=80, color="#ff7f0e").encode(
    x="Data_Hora:T",
    y="Subtotal_Verificado:Q",
    tooltip=[
        alt.Tooltip("Data_Hora:T", title="Mês", format="%B %Y"),
        alt.Tooltip("Subtotal_Verificado:Q", title="Faturamento", format=",.2f"),
        alt.Tooltip("Variacao:Q", title="Variação", format=".2f")
    ],
    size=alt.Size("Subtotal_Verificado:Q", scale=alt.Scale(range=[50, 500]))
)

# Combinar linha, área e pontos
chart_final = (area + linha + pontos).interactive()

st.altair_chart(chart_final, use_container_width=True)


# ===============================
# 10. Top 10 Clientes
# ===============================
st.subheader("🏆 Top 10 Clientes que Mais Faturaram")
top_clientes = (
    df_filtrado.groupby("Cliente")["Subtotal_Verificado"]
    .sum()
    .reset_index()
    .sort_values("Subtotal_Verificado", ascending=False)
    .head(10)
)
st.dataframe(top_clientes)

# ===============================
# 11. Distribuição de Faturamento por Forma de Pagamento (Pizza)
# ===============================
st.subheader("📊 Distribuição de Faturamento por Forma de Pagamento")
chart_pizza = alt.Chart(pagamentos).mark_arc().encode(
    theta=alt.Theta(field="Subtotal_Verificado", type="quantitative"),
    color=alt.Color(field="Forma_de_Pagamento_Simples", type="nominal"),
    tooltip=[alt.Tooltip("Forma_de_Pagamento_Simples"), alt.Tooltip("Subtotal_Verificado")]
)
st.altair_chart(chart_pizza, use_container_width=True)

# ===============================
# 12. Outliers de Faturamento
# ===============================
st.subheader("⚠️ Outliers de Faturamento")
outliers = df_filtrado[df_filtrado["Subtotal_Verificado"] > df_filtrado["Subtotal_Verificado"].quantile(0.95)]
st.dataframe(outliers)

# ===============================
# 13. Retenção de Clientes
# ===============================
st.subheader("🔄 Retenção de Clientes")
clientes_recorrentes = (
    df_filtrado.groupby("Cliente")["Codigo_da_Venda"]
    .nunique()
    .reset_index()
    .rename(columns={"Codigo_da_Venda": "Frequencia"})
    .sort_values("Frequencia", ascending=False)
)
st.dataframe(clientes_recorrentes)

# ===============================
# 14. Download CSV
# ===============================
st.download_button(
    label="📥 Baixar Dados Filtrados",
    data=df_filtrado.to_csv(index=False),
    file_name="dados_filtrados.csv",
    mime="text/csv"
)

# ===============================
# 15. Sidebar/Documentação
# ===============================
st.sidebar.title("Sobre o Projeto")
st.sidebar.info(
    "Este projeto analisa as formas de pagamento, identificando padrões e tendências "
    "para otimizar estratégias de negócios. Base de dados: [10k registros]."
)
  