"""DKidsFantasias · Dashboard Executivo de Vendas.

Ponto de entrada: define a navegação e delega cada página para views/.
"""

import streamlit as st

st.set_page_config(
    page_title="DKidsFantasias · Dashboard Executivo",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

paginas = st.navigation([
    st.Page("views/home.py", title="Visão Executiva", icon="🎭", default=True),
    st.Page("views/produtos.py", title="Produtos & Portfólio", icon="🧸"),
    st.Page("views/temporalidade.py", title="Temporalidade", icon="⏱️"),
    st.Page("views/pagamentos.py", title="Pagamentos", icon="💳"),
    st.Page("views/previsao.py", title="Previsão de Faturamento", icon="🔮"),
])
paginas.run()
