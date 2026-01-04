import pandas as pd

def create_features(df):

    # Forma de pagamento simplificada
    df['forma_pagamento'] = df['forma_de_pagamento'].str.strip().str.lower()

    # Data + hora (RFM e previsão)
    df['data_hora'] = pd.to_datetime(
        df['data'].astype(str) + ' ' + df['hora'].astype(str),
        errors='coerce'
    )

    # Semana do ano
    df['semana'] = df['data'].dt.isocalendar().week

    # Ticket (garantia)
    if 'ticket' not in df.columns:
        df['ticket'] = df['subtotal'] / df['qtd']

    return df
