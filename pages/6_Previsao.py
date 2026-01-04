# pages/6_Previsao_10k.py
import streamlit as st
import pandas as pd
import altair as alt
from core.forecast import forecast_faturamento_senior  # modelo XGBoost com intervalo de confiança

# --------------------- Checagem ---------------------
if 'df' not in st.session_state:
    st.error("Dados não carregados. Volte para a página inicial.")
    st.stop()

df = st.session_state.df.copy()
st.title("📈 Dashboard de Previsão de Faturamento - Premium 10k")

# --------------------- Histórico e Previsão ---------------------
serie, previsao, intervalo_inferior, intervalo_superior = forecast_faturamento_senior(df)
df_plot = serie.merge(previsao, on='data')
df_plot['Inferior'] = intervalo_inferior
df_plot['Superior'] = intervalo_superior

# --------------------- Gráfico Principal ---------------------
chart = alt.Chart(df_plot).encode(x='data:T')

line_real = chart.mark_line(color='#1f77b4', point=True).encode(
    y='Faturamento:Q', tooltip=['data:T', 'Faturamento:Q']
)
line_prev = chart.mark_line(color='#ff7f0e', point=True).encode(
    y='Faturamento_Previsto:Q', tooltip=['data:T', 'Faturamento_Previsto:Q']
)
band = chart.mark_area(opacity=0.3, color='#ff7f0e').encode(
    y='Inferior:Q', y2='Superior:Q'
)

st.subheader("📊 Histórico e Previsão de Faturamento Diário")
st.altair_chart((band + line_real + line_prev).interactive(), use_container_width=True)

# --------------------- Tabela com Diferença e Classificação ---------------------
df_table = df_plot.copy()
df_table['Diferença (%)'] = ((df_table['Faturamento_Previsto'] - df_table['Faturamento']) / df_table['Faturamento'] * 100).round(1)
def classifica(d):
    if abs(d) <= 10:
        return 'Bom ✅'
    elif abs(d) <= 30:
        return 'Médio ⚠️'
    else:
        return 'Ruim 🔴'
df_table['Classificação'] = df_table['Diferença (%)'].apply(classifica)
df_table_display = df_table[['data','Faturamento','Faturamento_Previsto','Diferença (%)','Classificação']]
df_table_display = df_table_display.rename(columns={'data':'Data','Faturamento':'Real (R$)','Faturamento_Previsto':'Previsto (R$)'})
st.subheader("📋 Tabela de Histórico + Previsão")
st.dataframe(df_table_display)

# --------------------- Resumo da Precisão ---------------------
total_dias = len(df_table_display)
bom = (df_table_display['Classificação'] == 'Bom ✅').sum()
medio = (df_table_display['Classificação'] == 'Médio ⚠️').sum()
ruim = (df_table_display['Classificação'] == 'Ruim 🔴').sum()

st.subheader("💡 Resumo da Precisão")
st.markdown(f"""
Total de dias analisados: **{total_dias}**  
Dias com previsão confiável (Bom ✅): **{bom} ({bom/total_dias*100:.1f}%)**  
Dias com atenção (Médio ⚠️): **{medio} ({medio/total_dias*100:.1f}%)**  
Dias com alerta (Ruim 🔴): **{ruim} ({ruim/total_dias*100:.1f}%)**
""")

# --------------------- Download CSV ---------------------
st.download_button(
    label="📥 Baixar CSV completo",
    data=df_table_display.to_csv(index=False),
    file_name="historico_previsao_premium.csv",
    mime="text/csv"
)

# --------------------- Melhores e Piores Dias ---------------------
top_dias = df_table_display.sort_values('Real (R$)', ascending=False).head(10)
bottom_dias = df_table_display.sort_values('Real (R$)', ascending=True).head(10)

st.subheader("🏆 Top 10 Melhores Dias")
st.dataframe(top_dias)

st.subheader("💔 Top 10 Piores Dias")
st.dataframe(bottom_dias)

# --------------------- Tendências Semanais ---------------------
df['Dia_Semana'] = df['Data_Hora'].dt.day_name()
semana = df.groupby('Dia_Semana')['Subtotal_Verificado'].sum().reindex(
    ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
).reset_index()
st.subheader("📅 Tendência Semanal de Faturamento")
chart_semana = alt.Chart(semana).mark_bar(color='#1f77b4').encode(
    x='Dia_Semana:N', y='Subtotal_Verificado:Q', tooltip=['Dia_Semana','Subtotal_Verificado']
)
st.altair_chart(chart_semana, use_container_width=True)


# --------------------- Distribuição de Confiabilidade ---------------------
st.subheader("📊 Distribuição da Precisão da Previsão")
chart_dist = alt.Chart(df_table).mark_bar().encode(
    x='Classificação:N', y='count()', color='Classificação:N',
    tooltip=['Classificação','count()']
)
st.altair_chart(chart_dist, use_container_width=True)

# --------------------- Insights Segmentados por Canal ---------------------
if 'Forma_de_Pagamento_Simples' in df.columns:
    pag = df.groupby('Forma_de_Pagamento_Simples')['Subtotal_Verificado'].sum().reset_index()
    st.subheader("💳 Distribuição de Faturamento por Forma de Pagamento")
    chart_pag = alt.Chart(pag).mark_bar().encode(
        x='Forma_de_Pagamento_Simples:N', y='Subtotal_Verificado:Q',
        color='Forma_de_Pagamento_Simples:N',
        tooltip=['Forma_de_Pagamento_Simples','Subtotal_Verificado']
    )
    st.altair_chart(chart_pag, use_container_width=True)

# --------------------- Explicação detalhada com storytelling ---------------------
st.markdown("""
### 📖 Como funciona a previsão de faturamento

Imagine que o faturamento da sua loja é como o fluxo de um rio.  
Alguns dias ele corre rápido (picos de venda), outros ele desacelera (dias mais fracos).  
Nosso objetivo é **antecipar o fluxo futuro do rio**, ou seja, prever o faturamento de cada dia.

#### 1️⃣ Observando o passado: aprendendo com os padrões
O modelo olha para o histórico de vendas diário e identifica:

- **Tendências**: crescimento, estabilidade ou queda ao longo do tempo  
- **Sazonalidade**: dias da semana ou meses com padrões recorrentes de vendas  
- **Picos e quedas**: eventos atípicos (promoções, feriados, campanhas)  

> Exemplo: todo sábado vende mais, todo dia 15 do mês vendas caem, às vezes campanhas geram picos.

#### 2️⃣ A magia do modelo XGBoost
O modelo aprende com cada detalhe do histórico, combinando:

- Tendências  
- Sazonalidades  
- Correções para picos atípicos  

Gerando uma **previsão diária** próxima do real.

#### 3️⃣ Medindo a confiabilidade
- **Diferença (%)**: erro entre previsão e real  
- **Classificação do dia**:
  - **Bom ✅** → erro pequeno, previsões confiáveis  
  - **Médio ⚠️** → atenção, previsões razoáveis  
  - **Ruim 🔴** → grande divergência, previsão menos confiável  

> Exemplo: Real = 1000, Previsto = 980 → Diferença 2% → Bom ✅

#### 4️⃣ Visualizando no gráfico
- **Linha azul** → faturamento real  
- **Linha laranja** → previsão XGBoost  
- **Sombreado laranja** → intervalo de confiança 95%  

Isso mostra claramente onde a previsão é confiável e onde é necessário atenção.

#### 5️⃣ Exemplo real

| Data       | Real (R$) | Previsto (R$) | Diferença (%) | Classificação |
|------------|-----------|---------------|---------------|---------------|
| 2025-06-02 | 155       | 160.73        | 3.7           | Bom ✅        |
| 2025-06-03 | 639.7     | 636.45        | -0.5          | Bom ✅        |
| 2025-06-04 | 156.9     | 172.08        | 9.7           | Bom ✅        |

> Interpretação: o modelo acertou bem a previsão, ideal para planejamento de estoque e fluxo de caixa.

#### 6️⃣ Por que isso importa
- Antecipar dias de **vendas altas ou baixas**  
- Ajustar estoque de forma eficiente  
- Planejar campanhas de marketing no momento certo  
- Reduzir riscos de falta de produtos ou excesso de estoque  
- Tomar decisões financeiras mais precisas

**📈 Resumo rápido**:  
- Azul = faturamento real  
- Laranja = previsão XGBoost  
- Sombreado laranja = incerteza (95%)  
- Diferença (%) = precisão da previsão  
- Classificação: Bom ✅, Médio ⚠️, Ruim 🔴  
- Tabela pronta para análise ou download
""")