def detectar_alertas(df):
    alertas = {}

    alertas['erros_subtotal'] = df[df['Erro_Subtotal']]
    alertas['outliers_ticket'] = df[df['Subtotal'] > df['Subtotal'].quantile(0.95)]

    produtos = (
        df.groupby('Produto')
        .agg(Faturamento=('Subtotal','sum'),
             Quantidade=('Qtd','sum'))
    )

    alertas['produtos_criticos'] = produtos[
        (produtos['Faturamento'] > produtos['Faturamento'].quantile(0.8)) &
        (produtos['Quantidade'] < produtos['Quantidade'].median())
    ]

    return alertas
