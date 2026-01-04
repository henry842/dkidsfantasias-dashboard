from core.preprocess import load_and_clean
from core.features import create_features

df = load_and_clean("data/vendas_raw.csv")
df = create_features(df)

df.to_csv("data/vendas_tratadas.csv", index=False)
print("Arquivo vendas_tratadas.csv gerado")
