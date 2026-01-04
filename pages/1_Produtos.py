import streamlit as st
import pandas as pd

st.title("🧸 Produtos – Performance, Valor e Risco")

# Proteção
if "df" not in st.session_state:
    st.error("Dataset não carregado.")
    st.stop()

df = st.session_state.df

# =========================
# KPIs PRINCIPAIS
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Produtos únicos", df["Produto"].nunique())
col2.metric("Categorias", df["Categoria"].nunique())
col3.metric("Faturamento total", f"R$ {df['Subtotal'].sum():,.2f}")
col4.metric("Ticket médio geral", f"R$ {df['Ticket'].mean():,.2f}")

st.divider()

# =========================
# FATURAMENTO
# =========================
st.subheader("💰 Produtos que sustentam o faturamento")

top_fat = (
    df.groupby("Produto", as_index=False)["Subtotal"]
      .sum()
      .sort_values("Subtotal", ascending=False)
)

top10 = top_fat.head(10)
top10["%_Faturamento"] = top10["Subtotal"] / df["Subtotal"].sum() * 100

st.dataframe(top10, use_container_width=True)

st.info(
    f"📌 Insight: Os 10 produtos acima representam "
    f"{top10['Subtotal'].sum() / df['Subtotal'].sum() * 100:.1f}% "
    "de todo o faturamento."
)

st.divider()

# =========================
# VOLUME
# =========================
st.subheader("📦 Produtos com maior giro (quantidade)")

top_qtd = (
    df.groupby("Produto", as_index=False)["Qtd"]
      .sum()
      .sort_values("Qtd", ascending=False)
      .head(10)
)

st.dataframe(top_qtd, use_container_width=True)

st.info(
    "📌 Insight: Produtos de alto volume nem sempre são os mais lucrativos. "
    "São essenciais para fluxo de caixa e visibilidade da loja."
)

st.divider()

# =========================
# TICKET
# =========================
st.subheader("🎟️ Produtos premium (alto ticket médio)")

ticket_prod = (
    df.groupby("Produto", as_index=False)["Ticket"]
      .mean()
      .sort_values("Ticket", ascending=False)
      .head(10)
)

st.dataframe(ticket_prod, use_container_width=True)

st.info(
    "📌 Insight: Esses produtos têm potencial para estratégias premium, "
    "exposição diferenciada e menor dependência de volume."
)

st.divider()

# =========================
# CATEGORIAS
# =========================
st.subheader("🗂️ Performance por categoria")

cat = (
    df.groupby("Categoria")
      .agg(
          Faturamento=("Subtotal", "sum"),
          Quantidade=("Qtd", "sum"),
          Ticket_Medio=("Ticket", "mean"),
          Produtos=("Produto", "nunique")
      )
      .sort_values("Faturamento", ascending=False)
)

st.dataframe(cat, use_container_width=True)

st.info(
    "📌 Insight: Categorias com alto faturamento e poucos produtos "
    "indicam dependência e risco. Diversificação pode ser estratégica."
)

st.divider()

# =========================
# RISCO E QUALIDADE
# =========================
st.subheader("⚠️ Produtos com sinais de risco")

riscos = (
    df.groupby("Produto")
      .agg(
          Outliers=("Outlier", "sum"),
          Erros_Subtotal=("Erro_Subtotal", "sum")
      )
      .sort_values(["Outliers", "Erros_Subtotal"], ascending=False)
      .head(10)
)

st.dataframe(riscos, use_container_width=True)

st.warning(
    "⚠️ Atenção: Produtos com muitos outliers ou erros de subtotal "
    "merecem revisão de preço, cadastro ou processo operacional."
)


#1️⃣ CONCENTRAÇÃO DE FATURAMENTO (RISCO OCULTO)
st.subheader("📊 Concentração de faturamento (risco de dependência)")

fat_prod = (
    df.groupby("Produto", as_index=False)["Subtotal"]
      .sum()
      .sort_values("Subtotal", ascending=False)
)

fat_prod["Faturamento_Acumulado_%"] = (
    fat_prod["Subtotal"].cumsum() / fat_prod["Subtotal"].sum() * 100
)

top5_pct = fat_prod.head(5)["Subtotal"].sum() / fat_prod["Subtotal"].sum() * 100

st.dataframe(fat_prod.head(15), use_container_width=True)

st.warning(
    f"⚠️ Os 5 principais produtos representam {top5_pct:.1f}% "
    "de todo o faturamento. Alta dependência aumenta risco operacional."
)


#2️⃣ CURVA ABC DE PRODUTOS (CLÁSSICO EXECUTIVO)
st.subheader("📈 Curva ABC de Produtos")

def class_abc(pct):
    if pct <= 80:
        return "A"
    elif pct <= 95:
        return "B"
    else:
        return "C"

fat_prod["Classe_ABC"] = fat_prod["Faturamento_Acumulado_%"].apply(class_abc)

abc_summary = fat_prod["Classe_ABC"].value_counts()

st.dataframe(abc_summary.rename("Quantidade de produtos"))

st.info(
    "📌 Produtos Classe A merecem foco total em estoque, preço e exposição. "
    "Classe C devem ter controle rigoroso de estoque."
)


#3️⃣ MAPA ESTRATÉGICO: VOLUME × TICKET

st.subheader("🧭 Mapa estratégico de produtos (Volume × Ticket)")

mapa = (
    df.groupby("Produto")
      .agg(
          Volume=("Qtd", "sum"),
          Ticket_Medio=("Ticket", "mean")
      )
)

vol_med = mapa["Volume"].median()
ticket_med = mapa["Ticket_Medio"].median()

def quadrante(row):
    if row["Volume"] >= vol_med and row["Ticket_Medio"] >= ticket_med:
        return "Estrela ⭐"
    elif row["Volume"] >= vol_med:
        return "Fluxo 📦"
    elif row["Ticket_Medio"] >= ticket_med:
        return "Premium 💎"
    else:
        return "Baixo impacto ⚠️"

mapa["Perfil"] = mapa.apply(quadrante, axis=1)

st.dataframe(
    mapa.sort_values("Ticket_Medio", ascending=False).head(15),
    use_container_width=True
)

st.info(
    "📌 Estrelas sustentam o negócio. Produtos Premium funcionam bem como "
    "âncoras de preço. Produtos de baixo impacto devem ser avaliados."
)


#4️⃣ CONSISTÊNCIA DE PREÇO (ERRO OU FRAUDE)

st.subheader("💸 Consistência de preço por produto")

preco = (
    df.groupby("Produto")["Valor_Unit"]
      .agg(["mean", "std", "count"])
      .rename(columns={"mean": "Preço_Médio", "std": "Desvio_Preço"})
      .sort_values("Desvio_Preço", ascending=False)
)

st.dataframe(preco.head(10), use_container_width=True)

st.warning(
    "⚠️ Produtos com alta variação de preço indicam possível erro de cadastro, "
    "desconto inconsistente ou falha operacional."
)


#5️⃣ PRODUTOS QUE PUXAM O TICKET DA VENDA

st.subheader("🛒 Produtos que elevam o ticket da venda")

ticket_pull = (
    df.groupby("Produto")
      .agg(
          Ticket_Medio=("Ticket", "mean"),
          Frequencia=("Codigo_da_Venda", "nunique")
      )
      .sort_values("Ticket_Medio", ascending=False)
)

st.dataframe(ticket_pull.head(10), use_container_width=True)

st.info(
    "📌 Produtos com alto ticket médio e baixa frequência são ideais como "
    "âncoras para combos e vendas adicionais."
)


#6️⃣ SAZONALIDADE DE PRODUTOS (FANTASIA = CRÍTICO)


st.subheader("🎭 Sazonalidade de produtos")

sazonal = (
    df.groupby(["Mes", "Produto"])["Qtd"]
      .sum()
      .reset_index()
      .sort_values("Qtd", ascending=False)
)

st.dataframe(sazonal.head(15), use_container_width=True)

st.info(
    "📌 Produtos fortemente sazonais devem ter estoque planejado por mês "
    "para evitar capital parado."
)



#7️⃣ PRODUTOS QUE FIDELIZAM CLIENTE

st.subheader("🔁 Produtos associados à fidelização")

fidel = (
    df.groupby("Produto")["Freq_Cliente"]
      .mean()
      .sort_values(ascending=False)
)

st.dataframe(fidel.head(10), use_container_width=True)

st.info(
    "📌 Produtos comprados por clientes recorrentes são estratégicos "
    "para retenção e programas de fidelidade."
)


# =========================
# CONCLUSÃO EXECUTIVA
# =========================
st.success(
    "📌 Conclusão Executiva:\n"
    "- Poucos produtos concentram grande parte do faturamento.\n"
    "- Existe clara separação entre produtos de fluxo, premium e baixo impacto.\n"
    "- Há sinais de inconsistência de preço e risco operacional em alguns itens.\n"
    "- Sazonalidade deve guiar estoque e compras.\n\n"
    "👉 Recomenda-se ações direcionadas por perfil de produto."
)
