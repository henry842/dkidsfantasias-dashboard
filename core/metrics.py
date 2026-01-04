import pandas as pd


def top_produtos(df, n=10):
    resultado = (
        df.groupby('produto', as_index=False)
        .agg(
            faturamento=('subtotal', 'sum'),
            quantidade=('qtd', 'sum'),
            ticket_medio=('ticket', 'mean')
        )
        .sort_values('faturamento', ascending=False)
        .head(n)
    )

    return resultado
