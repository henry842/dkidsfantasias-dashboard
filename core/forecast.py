"""Previsão de faturamento diário com XGBoost.

Metodologia:
1. Agrega a base em faturamento por dia de funcionamento.
2. Cria variáveis de calendário + defasagens (lags) e médias móveis.
3. Valida em holdout temporal (últimos dias nunca vistos no treino) e
   reporta MAE / WMAPE honestos, calculados só no holdout.
4. Re-treina com todo o histórico e projeta os próximos dias de forma
   iterativa, realimentando os lags com as próprias previsões.
5. Intervalo de confiança de 95% derivado do desvio dos resíduos do holdout.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

HOLDOUT_DIAS = 28
FEATURES = [
    "dia_semana", "dia_mes", "mes", "semana_ano", "fim_de_semana",
    "lag_1", "lag_7", "media_7", "media_28",
]


def _serie_diaria(df: pd.DataFrame) -> pd.DataFrame:
    serie = (
        df.groupby(df["Data_Hora"].dt.normalize())["Subtotal"]
        .sum()
        .rename("faturamento")
        .reset_index()
        .rename(columns={"Data_Hora": "data"})
        .sort_values("data")
        .reset_index(drop=True)
    )
    return serie


def _features_calendario(datas: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "dia_semana": datas.dt.weekday,
        "dia_mes": datas.dt.day,
        "mes": datas.dt.month,
        "semana_ano": datas.dt.isocalendar().week.astype(int),
        "fim_de_semana": (datas.dt.weekday >= 5).astype(int),
    })


def _montar_features(serie: pd.DataFrame) -> pd.DataFrame:
    feat = _features_calendario(serie["data"])
    feat["lag_1"] = serie["faturamento"].shift(1)
    feat["lag_7"] = serie["faturamento"].shift(7)
    feat["media_7"] = serie["faturamento"].shift(1).rolling(7, min_periods=3).mean()
    feat["media_28"] = serie["faturamento"].shift(1).rolling(28, min_periods=7).mean()
    feat["faturamento"] = serie["faturamento"]
    feat["data"] = serie["data"]
    return feat


def _novo_modelo() -> XGBRegressor:
    return XGBRegressor(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )


def prever_faturamento(df: pd.DataFrame, horizonte: int = 30) -> dict:
    """Retorna histórico com ajuste, métricas de validação e previsão futura."""
    serie = _serie_diaria(df)
    feat = _montar_features(serie).dropna(subset=["lag_1", "media_7"]).reset_index(drop=True)

    if len(feat) < HOLDOUT_DIAS + 30:
        raise ValueError("Histórico insuficiente para validar o modelo (mínimo ~2 meses de vendas).")

    # ------------------------- validação em holdout -------------------------
    treino, teste = feat.iloc[:-HOLDOUT_DIAS], feat.iloc[-HOLDOUT_DIAS:]
    modelo_val = _novo_modelo()
    modelo_val.fit(treino[FEATURES], treino["faturamento"])
    pred_teste = modelo_val.predict(teste[FEATURES])

    residuos = teste["faturamento"].values - pred_teste
    mae = mean_absolute_error(teste["faturamento"], pred_teste)
    wmape = np.abs(residuos).sum() / teste["faturamento"].sum() * 100
    desvio = float(np.std(residuos, ddof=1))
    banda = 1.96 * desvio
    cobertura = float(np.mean(np.abs(residuos) <= banda) * 100)

    # --------------------- re-treino com todo o histórico -------------------
    modelo = _novo_modelo()
    modelo.fit(feat[FEATURES], feat["faturamento"])

    historico = feat[["data", "faturamento"]].copy()
    historico["previsto"] = modelo.predict(feat[FEATURES])
    historico["conjunto"] = "Treino"
    historico.loc[historico.index[-HOLDOUT_DIAS:], "conjunto"] = "Validação"
    # No holdout, mostra a previsão honesta (do modelo que não viu esses dias)
    historico.loc[historico.index[-HOLDOUT_DIAS:], "previsto"] = pred_teste

    # ------------------------- projeção futura ------------------------------
    # A loja pode não abrir em todos os dias da semana: projeta apenas
    # nos dias que existem no histórico.
    dias_ativos = set(serie["data"].dt.weekday.unique())
    valores = serie.set_index("data")["faturamento"].copy()

    futuro_datas: list[pd.Timestamp] = []
    futuro_valores: list[float] = []
    data_atual = serie["data"].max()
    while len(futuro_datas) < horizonte:
        data_atual += pd.Timedelta(days=1)
        if data_atual.weekday() not in dias_ativos:
            continue
        cal = _features_calendario(pd.Series([data_atual]))
        historico_estendido = valores.sort_index()
        cal["lag_1"] = historico_estendido.iloc[-1]
        cal["lag_7"] = historico_estendido.iloc[-7] if len(historico_estendido) >= 7 else historico_estendido.mean()
        cal["media_7"] = historico_estendido.iloc[-7:].mean()
        cal["media_28"] = historico_estendido.iloc[-28:].mean()
        pred = float(modelo.predict(cal[FEATURES])[0])
        pred = max(pred, 0.0)
        futuro_datas.append(data_atual)
        futuro_valores.append(pred)
        valores.loc[data_atual] = pred  # realimenta lags

    futuro = pd.DataFrame({"data": futuro_datas, "previsto": futuro_valores})
    futuro["limite_inferior"] = (futuro["previsto"] - banda).clip(lower=0)
    futuro["limite_superior"] = futuro["previsto"] + banda

    return {
        "historico": historico,
        "futuro": futuro,
        "metricas": {
            "mae": float(mae),
            "wmape": float(wmape),
            "cobertura": cobertura,
            "holdout_dias": HOLDOUT_DIAS,
            "total_previsto": float(futuro["previsto"].sum()),
        },
    }
