"""Insights executivos calculados automaticamente a partir da base filtrada.

Nada aqui é texto fixo: todos os números vêm dos dados, então os insights
permanecem corretos com qualquer filtro aplicado.
"""

import pandas as pd

from core.ui import fmt_brl, fmt_pct


def _vendas(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega itens em vendas (cupons) únicas."""
    return df.groupby("Codigo_da_Venda").agg(
        Valor=("Subtotal", "sum"),
        Data=("Data", "first"),
    )


def kpis_gerais(df: pd.DataFrame) -> dict:
    vendas = _vendas(df)
    mensal = df.groupby("Ano_Mes")["Subtotal"].sum().sort_index()

    variacao_mm = None
    if len(mensal) >= 2:
        atual, anterior = mensal.iloc[-1], mensal.iloc[-2]
        if anterior > 0:
            variacao_mm = (atual - anterior) / anterior * 100

    return {
        "faturamento": df["Subtotal"].sum(),
        "n_vendas": len(vendas),
        "itens": int(df["Qtd"].sum()),
        "ticket_medio": vendas["Valor"].mean() if len(vendas) else 0.0,
        "itens_por_venda": df["Qtd"].sum() / len(vendas) if len(vendas) else 0.0,
        "produtos_ativos": df["Produto"].nunique(),
        "variacao_mm": variacao_mm,
    }


def insights_executivos(df: pd.DataFrame) -> list[dict]:
    """Retorna lista de insights: dicts com title, text e tone (ok/warn)."""
    out: list[dict] = []
    total = df["Subtotal"].sum()
    if total == 0 or df.empty:
        return out

    # 1. Concentração de faturamento (Pareto)
    fat_prod = df.groupby("Produto")["Subtotal"].sum().sort_values(ascending=False)
    acum = fat_prod.cumsum() / total * 100
    n_80 = int((acum <= 80).sum()) + 1
    pct_produtos = n_80 / len(fat_prod) * 100
    out.append({
        "title": "🎯 Concentração de faturamento",
        "text": (
            f"Apenas <b>{n_80} produtos</b> ({fmt_pct(pct_produtos, 0)} do portfólio) "
            f"geram 80% do faturamento. O líder é <b>{fat_prod.index[0]}</b>, com "
            f"{fmt_brl(fat_prod.iloc[0])} ({fmt_pct(fat_prod.iloc[0] / total * 100)})."
        ),
        "tone": "warn" if pct_produtos < 15 else "ok",
    })

    # 2. Melhor dia da semana
    dia = df.groupby("Dia_Semana_PT")["Subtotal"].sum().sort_values(ascending=False)
    if len(dia) >= 2:
        out.append({
            "title": "📅 Ritmo semanal",
            "text": (
                f"<b>{dia.index[0]}</b> é o dia mais forte ({fmt_pct(dia.iloc[0] / total * 100)} "
                f"do faturamento), seguido de <b>{dia.index[1]}</b>. "
                f"O dia mais fraco é <b>{dia.index[-1]}</b> — bom candidato a promoções de tráfego."
            ),
            "tone": "ok",
        })

    # 3. Pico de horário
    hora = df.groupby("Hora_do_Dia")["Subtotal"].sum().sort_values(ascending=False)
    if len(hora) >= 3:
        top3 = sorted(hora.head(3).index.tolist())
        pct_pico = hora.head(3).sum() / total * 100
        out.append({
            "title": "⏰ Janela de ouro",
            "text": (
                f"As faixas de <b>{top3[0]}h, {top3[1]}h e {top3[2]}h</b> concentram "
                f"{fmt_pct(pct_pico)} das vendas. Garanta equipe completa e caixa ágil nesses horários."
            ),
            "tone": "ok",
        })

    # 4. Forma de pagamento dominante
    pag = df.groupby("Forma_de_Pagamento_Simples")["Subtotal"].sum().sort_values(ascending=False)
    if len(pag) >= 1:
        out.append({
            "title": "💳 Meios de pagamento",
            "text": (
                f"<b>{pag.index[0]}</b> lidera com {fmt_pct(pag.iloc[0] / total * 100)} do faturamento. "
                + (
                    f"Pix representa {fmt_pct(pag.get('Pix', 0) / total * 100)} — "
                    "recebimento instantâneo e sem taxa de adquirente."
                    if "Pix" in pag.index else ""
                )
            ),
            "tone": "ok",
        })

    # 5. Tendência mensal
    mensal = df.groupby("Ano_Mes")["Subtotal"].sum().sort_index()
    if len(mensal) >= 3:
        ult3 = mensal.iloc[-3:]
        direcao = "crescimento" if ult3.iloc[-1] > ult3.iloc[0] else "queda"
        var = abs(ult3.iloc[-1] - ult3.iloc[0]) / ult3.iloc[0] * 100 if ult3.iloc[0] > 0 else 0
        out.append({
            "title": "📈 Tendência recente",
            "text": (
                f"Nos últimos 3 meses o faturamento apresenta <b>{direcao}</b> "
                f"de {fmt_pct(var)} — de {fmt_brl(ult3.iloc[0])} para {fmt_brl(ult3.iloc[-1])}."
            ),
            "tone": "ok" if direcao == "crescimento" else "warn",
        })

    return out
