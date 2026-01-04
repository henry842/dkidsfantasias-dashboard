# padroniza_csv_automatico.py
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
ORIGINAL_FILE = DATA_DIR / "cliente_original.csv"  # CSV que o cliente colocou
PADRONIZADO_FILE = DATA_DIR / "cliente_padronizado.csv"

# ------------------- Ler CSV -------------------
df = pd.read_csv(ORIGINAL_FILE)

# ------------------- Colunas Padrão -------------------
colunas_esperadas = [
    "Codigo_da_Venda","Produto","Qtd","Data","Hora","Cliente","Vendedor",
    "Forma_de_Pagamento","Valor_Unit","Subtotal","Subtotal_Verificado",
    "Diferenca_Subtotal","Dia_da_Semana","Mes","Ano","Hora_do_Dia",
    "Periodo_do_Dia","Ticket","Data_Hora","Outlier","Forma_de_Pagamento_Simples",
    "Semana_do_Ano","Trimestre","Feriado","Periodo_do_Mes","Tipo_Cliente",
    "Ticket_Cliente","Freq_Cliente","Categoria","Ticket_Medio_Forma",
    "Outlier_Ticket","Erro_Subtotal","Faturamento_Acumulado","Ranking_Cliente"
]

# ------------------- Criar colunas que faltam -------------------
for c in colunas_esperadas:
    if c not in df.columns:
        df[c] = None  # Pode ajustar para 0 se for numérico

# ------------------- Ajustes de tipos -------------------
if "Data" in df.columns:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
if "Hora" in df.columns:
    df["Hora"] = pd.to_datetime(df["Hora"], format="%H:%M:%S", errors="coerce").dt.time
if "Data_Hora" not in df.columns:
    df["Data_Hora"] = pd.to_datetime(df["Data"].astype(str) + " " + df["Hora"].astype(str), errors="coerce")

# ------------------- Campos calculados -------------------
df["Faturamento_Acumulado"] = df["Subtotal"].cumsum()
df["Ticket"] = df["Subtotal"]  # Exemplo simplificado
df["Dia_da_Semana"] = df["Data_Hora"].dt.day_name()
df["Mes"] = df["Data_Hora"].dt.month
df["Ano"] = df["Data_Hora"].dt.year

# ------------------- Salvar CSV padronizado -------------------
df.to_csv(PADRONIZADO_FILE, index=False)
print(f"✅ CSV padronizado pronto: {PADRONIZADO_FILE}")
