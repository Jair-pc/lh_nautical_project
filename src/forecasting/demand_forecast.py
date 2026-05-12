"""
Módulo de Previsão de Demanda — LH Nautical
============================================
Implementa modelos estatísticos para projeção de vendas futuras.

Modelos disponíveis:
  1. Média Móvel Simples      — baseline, baixa complexidade
  2. Regressão Linear         — captura tendência linear de crescimento
  3. Decomposição de Tendência — separa tendência, sazonalidade e resíduo

Nota metodológica:
  Com apenas 2 anos de histórico (2023-2024) e ~100 transações, os modelos
  aqui implementados são adequados para uma primeira camada analítica.
  Para produção, recomenda-se Prophet (Facebook) ou modelos ARIMA quando
  houver pelo menos 3 anos de dados mensais.
"""

import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)


def _preparar_serie_mensal(df: pd.DataFrame) -> pd.Series:
    """
    Converte a tabela fato_vendas em série temporal mensal de receita.

    Args:
        df: Tabela fato_vendas (Gold).

    Returns:
        Série indexada por período mensal (ano-mês).
    """
    df_ativo = df[df["status_venda"] == "concluida"].copy()
    df_ativo["periodo"] = df_ativo["data_venda"].dt.to_period("M")

    serie = (
        df_ativo
        .groupby("periodo")["receita_liquida"]
        .sum()
        .sort_index()
    )

    return serie


def media_movel(
    df: pd.DataFrame,
    janela: int = 3,
    periodos_futuros: int = 3,
) -> pd.DataFrame:
    """
    Previsão por Média Móvel Simples.

    A Média Móvel usa a média dos últimos N períodos como previsão
    para os próximos períodos. É o modelo mais simples, mas serve
    como benchmark para avaliar modelos mais complexos.

    Args:
        df:               Tabela fato_vendas.
        janela:           Número de meses para calcular a média (padrão: 3).
        periodos_futuros: Número de meses futuros a projetar.

    Returns:
        DataFrame com histórico + previsão, contendo colunas:
        periodo, receita_real, media_movel, previsao.
    """
    serie = _preparar_serie_mensal(df)

    resultado = pd.DataFrame({
        "periodo": serie.index.astype(str),
        "receita_real": serie.values,
    })

    resultado["media_movel"] = resultado["receita_real"].rolling(window=janela).mean().round(2)

    # Projeta os próximos períodos
    ultimo_periodo = serie.index[-1]
    media_base = serie.tail(janela).mean()

    projecoes = []
    for i in range(1, periodos_futuros + 1):
        proximo = ultimo_periodo + i
        projecoes.append({
            "periodo": str(proximo),
            "receita_real": np.nan,
            "media_movel": np.nan,
            "previsao": round(media_base, 2),
        })

    resultado["previsao"] = np.nan
    resultado_final = pd.concat([resultado, pd.DataFrame(projecoes)], ignore_index=True)

    logger.info(
        "[Forecast] Média Móvel (janela=%d): previsão para %d meses = R$ %.2f/mês",
        janela, periodos_futuros, media_base,
    )

    return resultado_final


def regressao_linear_forecast(
    df: pd.DataFrame,
    periodos_futuros: int = 6,
) -> Tuple[pd.DataFrame, dict]:
    """
    Previsão por Regressão Linear sobre tendência temporal.

    Usa o índice sequencial de meses como feature (X) e a receita
    líquida mensal como target (y). Captura tendência de crescimento
    ou queda ao longo do tempo.

    Args:
        df:               Tabela fato_vendas.
        periodos_futuros: Número de meses futuros a projetar.

    Returns:
        Tupla com:
        - DataFrame com histórico, valores ajustados e projeção
        - Dicionário com métricas do modelo (MAE, RMSE, R²)
    """
    serie = _preparar_serie_mensal(df)

    X = np.arange(len(serie)).reshape(-1, 1)
    y = serie.values

    model = LinearRegression()
    model.fit(X, y)

    y_pred = model.predict(X)

    mae  = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2   = model.score(X, y)

    metricas = {
        "coeficiente_angular": round(model.coef_[0], 2),
        "intercepto":          round(model.intercept_, 2),
        "mae":  round(mae, 2),
        "rmse": round(rmse, 2),
        "r2":   round(r2, 4),
        "interpretacao": (
            f"A receita {'cresce' if model.coef_[0] > 0 else 'decresce'} "
            f"R$ {abs(model.coef_[0]):.2f} por mês em média."
        ),
    }

    # Constrói DataFrame de resultado
    historico = pd.DataFrame({
        "periodo":      serie.index.astype(str),
        "receita_real": serie.values.round(2),
        "ajuste_modelo": y_pred.round(2),
        "tipo": "historico",
    })

    # Projeta períodos futuros
    X_futuro = np.arange(len(serie), len(serie) + periodos_futuros).reshape(-1, 1)
    y_futuro = model.predict(X_futuro)

    ultimo_periodo = serie.index[-1]
    futuros = pd.DataFrame({
        "periodo":      [str(ultimo_periodo + i) for i in range(1, periodos_futuros + 1)],
        "receita_real": np.nan,
        "ajuste_modelo": y_futuro.round(2),
        "tipo": "previsao",
    })

    resultado = pd.concat([historico, futuros], ignore_index=True)

    logger.info(
        "[Forecast] Regressão Linear | R²=%.4f | MAE=R$ %.2f | Tendência=R$ %.2f/mês",
        r2, mae, model.coef_[0],
    )

    return resultado, metricas


def gerar_relatorio_previsao(df: pd.DataFrame) -> None:
    """
    Gera e exibe um relatório completo de previsão de demanda.

    Combina os modelos disponíveis e apresenta resultados de forma
    acessível para stakeholders não-técnicos (Marina Costa, Sr. Almir).

    Args:
        df: Tabela fato_vendas.
    """
    print("\n" + "=" * 60)
    print("  RELATÓRIO DE PREVISÃO DE DEMANDA — LH Nautical")
    print("=" * 60)

    # Média Móvel
    mm_df = media_movel(df, janela=3, periodos_futuros=3)
    previsoes_mm = mm_df[mm_df["previsao"].notna()]
    print("\n[Modelo 1] Média Móvel (janela = 3 meses)")
    print("-" * 40)
    for _, row in previsoes_mm.iterrows():
        print(f"  {row['periodo']} -> R$ {row['previsao']:>10,.2f}")

    # Regressão Linear
    rl_df, metricas = regressao_linear_forecast(df, periodos_futuros=6)
    previsoes_rl = rl_df[rl_df["tipo"] == "previsao"]
    print("\n[Modelo 2] Regressão Linear")
    print(f"  R² = {metricas['r2']} | MAE = R$ {metricas['mae']:,.2f}")
    print(f"  Tendência: {metricas['interpretacao']}")
    print("-" * 40)
    for _, row in previsoes_rl.iterrows():
        print(f"  {row['periodo']} -> R$ {row['ajuste_modelo']:>10,.2f}")

    print("\n[Aviso] Com 2 anos de histórico, use estas previsões como")
    print("  orientação direcional, não como números exatos.")
    print("  Próximo passo recomendado: implementar Prophet ou ARIMA")
    print("  quando houver >= 3 anos de dados mensais.\n")
