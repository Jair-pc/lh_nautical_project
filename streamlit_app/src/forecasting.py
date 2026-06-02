import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from dateutil.relativedelta import relativedelta


def _periodo_to_date(period_str: str) -> pd.Timestamp:
    return pd.to_datetime(period_str + "-01")


def moving_average(df_mensal: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    df = df_mensal.sort_values("ano_mes").copy()
    df["ma"] = df["receita"].rolling(window=window, min_periods=1).mean()
    return df[["ano_mes", "ma"]]


def linear_forecast(df_mensal: pd.DataFrame, n_ahead: int = 6) -> pd.DataFrame:
    df = df_mensal.sort_values("ano_mes").copy()
    df["t"] = range(len(df))

    X = df[["t"]].values
    y = df["receita"].values

    model = LinearRegression().fit(X, y)

    last_period = _periodo_to_date(df["ano_mes"].iloc[-1])
    future_periods = [
        (last_period + relativedelta(months=i + 1)).strftime("%Y-%m")
        for i in range(n_ahead)
    ]
    t_future = np.arange(len(df), len(df) + n_ahead).reshape(-1, 1)

    preds = model.predict(t_future)

    residuals = y - model.predict(X)
    std_err   = residuals.std()

    result = pd.DataFrame({
        "ano_mes":  future_periods,
        "previsao": preds,
        "lower":    preds - 1.5 * std_err,
        "upper":    preds + 1.5 * std_err,
    })
    result["lower"] = result["lower"].clip(lower=0)
    return result


def forecast_report(df_mensal: pd.DataFrame, n_ahead: int = 6) -> dict:
    df = df_mensal.sort_values("ano_mes").copy()
    df["t"] = range(len(df))

    X = df[["t"]].values
    y = df["receita"].values
    model = LinearRegression().fit(X, y)

    slope    = model.coef_[0]
    r2       = model.score(X, y)
    media_3m = df["receita"].iloc[-3:].mean() if len(df) >= 3 else df["receita"].mean()

    tendencia = "crescimento" if slope > 0 else "queda"

    return {
        "slope":     slope,
        "r2":        r2,
        "media_3m":  media_3m,
        "tendencia": tendencia,
        "n_obs":     len(df),
    }
