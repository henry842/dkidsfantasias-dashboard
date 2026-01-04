import pandas as pd

def load_and_clean(path):
    df = pd.read_csv(path, encoding="utf-8")

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(".", "", regex=False)
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )

    df['valor_unit'] = df['valor_unit'].astype(str).str.replace('R$', '', regex=False).str.replace(',', '.').astype(float)
    df['subtotal'] = df['subtotal'].astype(str).str.replace('R$', '', regex=False).str.replace(',', '.').astype(float)

    df['qtd'] = pd.to_numeric(df['qtd'], errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['hora'] = pd.to_datetime(df['hora'], format='%H:%M', errors='coerce').dt.time

    df = df.drop_duplicates(subset=['codigo_da_venda'])
    df = df.dropna(subset=['produto', 'qtd', 'valor_unit', 'subtotal', 'data'])

    return df
