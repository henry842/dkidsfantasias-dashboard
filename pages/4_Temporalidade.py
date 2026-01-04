import streamlit as st

import pandas as pd
import streamlit as st
import altair as alt  # se estiver usando Altair para gráficos

from prophet import Prophet
import pandas as pd
df = st.session_state.df.copy()

df = st.session_state.df

st.title("⏱️ Temporalidade")

vendas_dia = df.groupby("Dia_da_Semana")["Subtotal"].sum()

st.bar_chart(vendas_dia)

# vendas_mes = df.groupby("Mes")["Subtotal"].sum()

# st.line_chart(vendas_mes)


vendas_ano = df.groupby("Ano")["Subtotal"].sum()
st.subheader("📅 Faturamento por Ano")
st.bar_chart(vendas_ano)

vendas_trimestre = df.groupby("Trimestre")["Subtotal"].sum()
st.subheader("📅 Faturamento por Trimestre")
st.bar_chart(vendas_trimestre)


df['Faturamento_Acumulado'] = df['Subtotal'].cumsum()
st.subheader("📈 Faturamento Acumulado")
st.line_chart(df['Faturamento_Acumulado'])


st.subheader("🏆 Dias com Maior Faturamento")
top_dias = df.groupby("Dia_da_Semana")["Subtotal"].sum().sort_values(ascending=False)
st.dataframe(top_dias)

st.subheader("🏆 Meses com Maior Faturamento")
top_meses = df.groupby("Mes")["Subtotal"].sum().sort_values(ascending=False)
st.dataframe(top_meses)


vendas_feriados = df.groupby("Feriado")["Subtotal"].sum()
st.subheader("🎉 Faturamento em Dias de Feriado")
st.bar_chart(vendas_feriados)



vendas_hora = df.groupby("Hora")["Subtotal"].sum()
st.subheader("⏰ Faturamento por Hora do Dia")
st.line_chart(vendas_hora)



vendas_periodo = df.groupby("Periodo_do_Dia")["Subtotal"].sum()
st.subheader("🌅 Faturamento por Período do Dia")
st.bar_chart(vendas_periodo)



vendas_tipo_cliente = df.groupby("Tipo_Cliente")["Subtotal"].sum()
st.subheader("👥 Faturamento por Tipo de Cliente")
st.bar_chart(vendas_tipo_cliente)

 
vendas_pagamento = df.groupby("Forma_de_Pagamento_Simples")["Subtotal"].sum()
st.subheader("💳 Faturamento por Forma de Pagamento")
st.bar_chart(vendas_pagamento)


import altair as alt


# 🔹 Normalização de nomes para garantir compatibilidade
df = st.session_state.df.copy()
# Se ainda não houver Faturamento, criamos com Subtotal_Verificado
if 'Faturamento' not in df.columns:
    if 'Subtotal_Verificado' in df.columns:
        df['Faturamento'] = df['Subtotal_Verificado']
    elif 'Subtotal' in df.columns:
        df['Faturamento'] = df['Subtotal']
    else:
        st.error("Não foi possível identificar coluna de faturamento!")
        st.stop()

# Se não houver Faturamento_Previsto (previsão), criamos coluna placeholder
if 'Faturamento_Previsto' not in df.columns:
    df['Faturamento_Previsto'] = df['Faturamento']  # provisório até rodar o modelo

# Garantir Ano e Mês como colunas numéricas
if 'Ano' not in df.columns or 'Mes' not in df.columns:
    df['Data_Hora'] = pd.to_datetime(df.get('Data_Hora', df.get('data', pd.NaT)), errors='coerce')
    df['Ano'] = df['Data_Hora'].dt.year
    df['Mes'] = df['Data_Hora'].dt.month


# --------------------- Gráfico Tendência Mensal por Ano ---------------------
st.subheader("📊 Tendência de Faturamento Mensal por Ano")

# Preparar DataFrame agregado
df_mes = df.groupby(['Ano','Mes']).agg({
    'Faturamento':'sum',
    'Faturamento_Previsto':'sum'
}).reset_index()

# Criação do gráfico Altair
chart_mes = alt.Chart(df_mes).encode(
    x=alt.X('Mes:O', title='Mês'),
    y=alt.Y('Faturamento:Q', title='Faturamento (R$)'),
    color=alt.Color('Ano:N', title='Ano'),
    tooltip=[
        alt.Tooltip('Ano:N', title='Ano'),
        alt.Tooltip('Mes:O', title='Mês'),
        alt.Tooltip('Faturamento:Q', title='Faturamento Real (R$)'),
        alt.Tooltip('Faturamento_Previsto:Q', title='Previsto (R$)')
    ]
)

# Linha de faturamento real
line_real_mes = chart_mes.mark_line(point=True, strokeWidth=2)

# Render do gráfico
st.altair_chart(line_real_mes.interactive(), use_container_width=True)



vendas_categoria = df.groupby(["Categoria", "Mes"])["Subtotal"].sum().reset_index()
chart = alt.Chart(vendas_categoria).mark_bar().encode(
    x="Mes:O",
    y="Subtotal:Q",
    color="Categoria:N",
    tooltip=["Categoria", "Mes", "Subtotal"]
).properties(title="Faturamento por Categoria e Mês")
st.altair_chart(chart, use_container_width=True)



st.success(
    "📌 **Insights Executivos:**\n"
    "- O faturamento é mais alto nos meses de alta temporada (ex.: dezembro).\n"
    "- Os períodos do dia com maior faturamento são [manhã/tarde].\n"
    "- Clientes do tipo [VIP] geram maior receita.\n"
    "- A forma de pagamento mais utilizada é [Cartão de Crédito].\n"
    "👉 Recomenda-se focar em campanhas promocionais nos horários e dias de maior movimento."
)



from prophet import Prophet

df_prophet = df.groupby("Data")["Subtotal"].sum().reset_index()
df_prophet.columns = ["ds", "y"]

model = Prophet()
model.fit(df_prophet)

future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

st.subheader("🔮 Previsão de Faturamento")
st.line_chart(forecast[["ds", "yhat"]].set_index("ds"))


cliente_selecionado = st.selectbox("Selecione um Cliente", df["Cliente"].unique())
vendas_cliente = df[df["Cliente"] == cliente_selecionado]
st.subheader(f"📊 Faturamento do Cliente: {cliente_selecionado}")
st.dataframe(vendas_cliente)


import pandas as pd
import streamlit as st

# Supondo que df já exista
df = st.session_state.df.copy()

# Converter coluna para datetime (garante que comparações funcionem)
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

# Inputs do usuário
data_inicio = st.date_input("Data de Início", value=df["Data"].min())
data_fim = st.date_input("Data de Fim", value=df["Data"].max())

# Filtrar de forma segura
df_filtrado = df[
    (df["Data"] >= pd.to_datetime(data_inicio)) &
    (df["Data"] <= pd.to_datetime(data_fim))
]

st.subheader("📅 Dados Filtrados")
st.dataframe(df_filtrado)



st.sidebar.title("Sobre o Projeto")
st.sidebar.info(
    "Este projeto analisa a temporalidade das vendas, identificando padrões e tendências "
    "para otimizar estratégias de negócios. Base de dados: [10k registros]."
)