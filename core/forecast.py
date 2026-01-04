# core/forecast.py
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# core/forecast.py
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

def forecast_faturamento_senior(df):
    """
    Retorna previsão de faturamento diária usando XGBoost.
    Saída: 
        serie: DataFrame histórico diário
        previsao: DataFrame previsão diária
        intervalo_inferior: série do limite inferior 95%
        intervalo_superior: série do limite superior 95%
    """
    # ---------------------
    # 1. Preparar histórico diário
    # ---------------------
    df = df.copy()
    df['Data_Hora'] = pd.to_datetime(df['Data_Hora'], errors='coerce')
    df = df.dropna(subset=['Data_Hora', 'Subtotal_Verificado'])

    # Agrupar por dia
    serie = df.groupby(df['Data_Hora'].dt.date)['Subtotal_Verificado'].sum().reset_index()
    serie.columns = ['data', 'Faturamento']
    serie['data'] = pd.to_datetime(serie['data'])

    # ---------------------
    # 2. Criar features temporais
    # ---------------------
    serie['dia_semana'] = serie['data'].dt.weekday
    serie['dia_mes'] = serie['data'].dt.day
    serie['mes'] = serie['data'].dt.month
    serie['ano'] = serie['data'].dt.year
    serie['trimestre'] = serie['data'].dt.quarter

    X = serie[['dia_semana','dia_mes','mes','ano','trimestre']]
    y = serie['Faturamento']

    # ---------------------
    # 3. Treinar XGBoost
    # ---------------------
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, shuffle=False)
    model = XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Previsão para todo histórico
    y_pred = model.predict(X)
    serie['Faturamento_Previsto'] = y_pred

    # ---------------------
    # 4. Intervalo de confiança
    # ---------------------
    # Usar erro absoluto médio como proxy
    mae = mean_absolute_error(y, y_pred)
    intervalo_inferior = serie['Faturamento_Previsto'] - 1.96*mae
    intervalo_superior = serie['Faturamento_Previsto'] + 1.96*mae

    # ---------------------
    # 5. Retornar DataFrames
    # ---------------------
    previsao = serie[['data','Faturamento_Previsto']].copy()
    intervalo_inferior = intervalo_inferior
    intervalo_superior = intervalo_superior

    return serie[['data','Faturamento']], previsao, intervalo_inferior, intervalo_superior
