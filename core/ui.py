"""Identidade visual do dashboard: CSS, cards de KPI, tema dos gráficos e formatação pt-BR."""

import altair as alt
import streamlit as st

# Paleta oficial do projeto
PRIMARY = "#6C3BD9"
SECONDARY = "#F72585"
ACCENT = "#FFB703"
TEAL = "#2EC4B6"
SKY = "#4CC9F0"
PALETTE = [PRIMARY, SECONDARY, ACCENT, TEAL, SKY, "#B5179E", "#FF6B6B", "#8AC926"]

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Sora', sans-serif !important; letter-spacing: -0.02em; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1D1B2E 0%, #2A2350 100%);
}
section[data-testid="stSidebar"] * { color: #EDEAFB !important; }
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background-color: #6C3BD9 !important;
}

.dk-hero {
    background: linear-gradient(120deg, #6C3BD9 0%, #9D4EDD 55%, #F72585 130%);
    border-radius: 18px;
    padding: 28px 34px 24px 34px;
    color: white;
    margin-bottom: 6px;
    box-shadow: 0 12px 30px rgba(108, 59, 217, 0.25);
}
.dk-hero .dk-kicker {
    font-size: 0.78rem; font-weight: 600; letter-spacing: 0.18em;
    text-transform: uppercase; opacity: 0.85; margin-bottom: 4px;
}
.dk-hero h1 {
    font-family: 'Sora', sans-serif; font-size: 1.9rem; font-weight: 800;
    margin: 0 0 6px 0; color: white;
}
.dk-hero .dk-sub { font-size: 0.95rem; opacity: 0.92; margin: 0; }

.dk-kpis { display: flex; gap: 14px; flex-wrap: wrap; margin: 18px 0 8px 0; }
.dk-card {
    flex: 1 1 160px;
    background: white;
    border: 1px solid #EBE7F7;
    border-radius: 14px;
    padding: 16px 18px 14px 18px;
    box-shadow: 0 3px 14px rgba(38, 36, 58, 0.05);
    border-top: 3px solid var(--dk-accent, #6C3BD9);
}
.dk-card .dk-label {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #8B87A0; margin-bottom: 6px;
}
.dk-card .dk-value {
    font-family: 'Sora', sans-serif; font-size: 1.45rem; font-weight: 700;
    color: #26243A; line-height: 1.15;
}
.dk-card .dk-delta { font-size: 0.78rem; font-weight: 600; margin-top: 5px; }
.dk-card .dk-delta.up { color: #14975B; }
.dk-card .dk-delta.down { color: #D6336C; }
.dk-card .dk-delta.neutral { color: #8B87A0; }

.dk-insight {
    background: white;
    border: 1px solid #EBE7F7;
    border-left: 4px solid var(--dk-accent, #6C3BD9);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(38, 36, 58, 0.04);
}
.dk-insight .dk-ins-title {
    font-weight: 700; font-size: 0.9rem; color: #26243A; margin-bottom: 3px;
}
.dk-insight .dk-ins-text { font-size: 0.87rem; color: #55516B; line-height: 1.45; }

.dk-section {
    font-family: 'Sora', sans-serif; font-size: 1.12rem; font-weight: 700;
    color: #26243A; margin: 26px 0 4px 0;
    display: flex; align-items: center; gap: 8px;
}
.dk-section-sub { font-size: 0.86rem; color: #8B87A0; margin-bottom: 10px; }

.dk-footer {
    margin-top: 42px; padding-top: 16px; border-top: 1px solid #EBE7F7;
    font-size: 0.78rem; color: #A8A4BC; text-align: center;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, kicker: str = "DKidsFantasias · Inteligência de Vendas") -> None:
    st.markdown(
        f"""
        <div class="dk-hero">
            <div class="dk-kicker">{kicker}</div>
            <h1>{title}</h1>
            <p class="dk-sub">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(cards: list[dict]) -> None:
    """Renderiza uma linha de cards. Cada card: label, value, delta (opcional), direction (up/down/neutral), accent."""
    html = ['<div class="dk-kpis">']
    for c in cards:
        accent = c.get("accent", PRIMARY)
        delta_html = ""
        if c.get("delta"):
            direction = c.get("direction", "neutral")
            arrow = {"up": "▲", "down": "▼", "neutral": "•"}[direction]
            delta_html = f'<div class="dk-delta {direction}">{arrow} {c["delta"]}</div>'
        html.append(
            f'<div class="dk-card" style="--dk-accent:{accent}">'
            f'<div class="dk-label">{c["label"]}</div>'
            f'<div class="dk-value">{c["value"]}</div>{delta_html}</div>'
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def insight_card(title: str, text: str, accent: str = PRIMARY) -> None:
    st.markdown(
        f"""
        <div class="dk-insight" style="--dk-accent:{accent}">
            <div class="dk-ins-title">{title}</div>
            <div class="dk-ins-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="dk-section">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="dk-section-sub">{subtitle}</div>', unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        '<div class="dk-footer">DKidsFantasias · Dashboard Executivo de Vendas · '
        "Desenvolvido com Python + Streamlit</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def themed(chart: alt.Chart) -> alt.Chart:
    """Aplica o tema visual padrão a um gráfico Altair (inclusive em camadas)."""
    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#6B6785",
            titleColor="#3A3752",
            gridColor="#EEEBF7",
            domainColor="#E0DCEF",
            labelFontSize=12,
            titleFontSize=12,
            titleFontWeight=600,
        )
        .configure_legend(labelColor="#6B6785", titleColor="#3A3752", labelFontSize=12)
    )


def render(chart: alt.Chart, height: int | None = None) -> None:
    if height:
        chart = chart.properties(height=height)
    st.altair_chart(themed(chart), use_container_width=True, theme=None)


# ---------------------------------------------------------------------------
# Formatação pt-BR
# ---------------------------------------------------------------------------

def _sep_ptbr(s: str) -> str:
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_brl(v: float, decimals: int = 2) -> str:
    return "R$ " + _sep_ptbr(f"{v:,.{decimals}f}")


def fmt_brl_compact(v: float) -> str:
    if abs(v) >= 1_000_000:
        return "R$ " + _sep_ptbr(f"{v / 1_000_000:,.1f}") + " mi"
    if abs(v) >= 1_000:
        return "R$ " + _sep_ptbr(f"{v / 1_000:,.1f}") + " mil"
    return fmt_brl(v, 0)


def fmt_int(v: float) -> str:
    return _sep_ptbr(f"{int(v):,}")


def fmt_pct(v: float, decimals: int = 1) -> str:
    return _sep_ptbr(f"{v:,.{decimals}f}") + "%"
