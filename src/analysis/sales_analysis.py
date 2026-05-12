"""
Módulo de Análise de Vendas — LH Nautical
==========================================
Centraliza todas as métricas e análises de negócio derivadas da
tabela fato_vendas (camada Gold).

Métricas disponíveis:
  - Faturamento total e mensal
  - Ticket médio por transação e por cliente
  - Margem por produto e por categoria
  - Ranking de produtos (volume, receita, lucro)
  - Ranking de clientes (mais lucrativos)
  - Vendas por canal e por dia da semana
  - Análise de sazonalidade (mensal/trimestral)
  - Produtos com prejuízo (margem negativa)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Métricas de Faturamento
# ---------------------------------------------------------------------------

def faturamento_total(df: pd.DataFrame) -> dict:
    """
    Calcula o faturamento geral do período.

    Args:
        df: Tabela fato_vendas (Gold).

    Returns:
        Dicionário com receita_bruta, receita_liquida, lucro_bruto
        e margem_media_pct do período completo.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    return {
        "receita_bruta":    round(df_ativo["receita_bruta"].sum(), 2),
        "receita_liquida":  round(df_ativo["receita_liquida"].sum(), 2),
        "lucro_bruto":      round(df_ativo["lucro_bruto"].sum(), 2),
        "margem_media_pct": round(df_ativo["margem_pct"].mean(), 2),
        "total_transacoes": len(df_ativo),
        "total_itens":      int(df_ativo["quantidade"].sum()),
    }


def faturamento_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega faturamento por ano e mês para análise de tendência.

    Args:
        df: Tabela fato_vendas.

    Returns:
        DataFrame com colunas: ano, mes, receita_liquida, lucro_bruto,
        margem_pct, num_transacoes — ordenado cronologicamente.
    """
    df_ativo = df[df["status_venda"] == "concluida"].copy()

    mensal = (
        df_ativo
        .groupby(["ano", "mes"])
        .agg(
            receita_liquida=("receita_liquida", "sum"),
            lucro_bruto=("lucro_bruto", "sum"),
            num_transacoes=("id_venda", "count"),
            itens_vendidos=("quantidade", "sum"),
        )
        .reset_index()
        .sort_values(["ano", "mes"])
    )

    mensal["margem_pct"] = (
        mensal["lucro_bruto"] / mensal["receita_liquida"] * 100
    ).round(2)

    # Variação percentual mês a mês
    mensal["var_receita_pct"] = mensal["receita_liquida"].pct_change() * 100

    return mensal.round(2)


def ticket_medio(df: pd.DataFrame) -> dict:
    """
    Calcula o ticket médio por transação e por cliente.

    Args:
        df: Tabela fato_vendas.

    Returns:
        Dicionário com ticket_por_transacao e ticket_por_cliente.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    ticket_transacao = df_ativo["receita_liquida"].mean()
    ticket_cliente   = (
        df_ativo.groupby("id_cliente")["receita_liquida"].sum().mean()
    )

    return {
        "ticket_medio_transacao": round(ticket_transacao, 2),
        "ticket_medio_cliente":   round(ticket_cliente, 2),
    }


# ---------------------------------------------------------------------------
# Análise de Produtos
# ---------------------------------------------------------------------------

def margem_por_produto(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Calcula receita, lucro e margem agrupados por produto.

    Args:
        df:    Tabela fato_vendas.
        top_n: Número de produtos a retornar (por receita).

    Returns:
        DataFrame com ranking de produtos por receita líquida,
        contendo também lucro e margem percentual.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    resultado = (
        df_ativo
        .groupby("id_produto")
        .agg(
            receita_liquida=("receita_liquida", "sum"),
            lucro_bruto=("lucro_bruto", "sum"),
            itens_vendidos=("quantidade", "sum"),
            num_transacoes=("id_venda", "count"),
        )
        .reset_index()
    )

    resultado["margem_pct"] = (
        resultado["lucro_bruto"] / resultado["receita_liquida"] * 100
    ).round(2)

    return resultado.sort_values("receita_liquida", ascending=False).head(top_n).round(2)


def produtos_com_prejuizo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica produtos onde o lucro acumulado é negativo.

    Esses produtos são candidatos à revisão de precificação ou
    descontinuação, e devem ser apresentados à diretoria.

    Args:
        df: Tabela fato_vendas.

    Returns:
        DataFrame com produtos em situação de prejuízo,
        ordenado pelo pior resultado financeiro.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    por_produto = (
        df_ativo
        .groupby("id_produto")
        .agg(
            receita_liquida=("receita_liquida", "sum"),
            lucro_bruto=("lucro_bruto", "sum"),
            itens_vendidos=("quantidade", "sum"),
        )
        .reset_index()
    )

    por_produto["margem_pct"] = (
        por_produto["lucro_bruto"] / por_produto["receita_liquida"] * 100
    ).round(2)

    return (
        por_produto[por_produto["lucro_bruto"] < 0]
        .sort_values("lucro_bruto")
        .round(2)
    )


def ranking_produtos(df: pd.DataFrame, criterio: str = "receita", top_n: int = 10) -> pd.DataFrame:
    """
    Retorna o ranking de produtos por critério escolhido.

    Args:
        df:       Tabela fato_vendas.
        criterio: 'receita' | 'lucro' | 'volume' (quantidade).
        top_n:    Número de produtos no ranking.

    Returns:
        DataFrame com os top N produtos pelo critério.
    """
    coluna_map = {
        "receita": "receita_liquida",
        "lucro":   "lucro_bruto",
        "volume":  "quantidade",
    }

    if criterio not in coluna_map:
        raise ValueError(f"Critério inválido: {criterio}. Use: {list(coluna_map)}")

    col = coluna_map[criterio]
    df_ativo = df[df["status_venda"] == "concluida"]

    return (
        df_ativo
        .groupby("id_produto")[col]
        .sum()
        .reset_index()
        .sort_values(col, ascending=False)
        .head(top_n)
        .rename(columns={col: criterio})
        .round(2)
    )


# ---------------------------------------------------------------------------
# Análise de Clientes
# ---------------------------------------------------------------------------

def ranking_clientes(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Ranking de clientes por valor total de compras e lucratividade.

    Args:
        df:    Tabela fato_vendas.
        top_n: Número de clientes no ranking.

    Returns:
        DataFrame com os clientes mais valiosos para o negócio.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    return (
        df_ativo
        .groupby("id_cliente")
        .agg(
            receita_liquida=("receita_liquida", "sum"),
            lucro_bruto=("lucro_bruto", "sum"),
            num_compras=("id_venda", "count"),
            itens_comprados=("quantidade", "sum"),
        )
        .reset_index()
        .sort_values("receita_liquida", ascending=False)
        .head(top_n)
        .round(2)
    )


# ---------------------------------------------------------------------------
# Análise Temporal e Sazonalidade
# ---------------------------------------------------------------------------

def vendas_por_dia_semana(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega receita e volume de vendas por dia da semana.

    Útil para identificar os melhores dias para promoções e
    reforço de equipe na loja física.

    Args:
        df: Tabela fato_vendas.

    Returns:
        DataFrame com receita e transações por dia da semana.
    """
    df_ativo = df[df["status_venda"] == "concluida"].copy()

    # Ordena pelo dia da semana correto (segunda = 0)
    ordem = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    labels_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    resultado = (
        df_ativo
        .groupby("dia_semana")
        .agg(
            receita_liquida=("receita_liquida", "sum"),
            num_transacoes=("id_venda", "count"),
            ticket_medio=("receita_liquida", "mean"),
        )
        .reset_index()
    )

    resultado["dia_semana"] = pd.Categorical(resultado["dia_semana"], categories=ordem, ordered=True)
    resultado = resultado.sort_values("dia_semana")
    resultado["dia_semana_pt"] = labels_pt[:len(resultado)]

    return resultado.round(2)


def analise_sazonalidade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analisa padrões sazonais por trimestre e mês do ano.

    A LH Nautical é fortemente sazonal: verão no sul (dez-fev)
    coincide com alta demanda por acessórios náuticos.

    Args:
        df: Tabela fato_vendas.

    Returns:
        DataFrame com receita média por mês, agregada entre os anos.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    return (
        df_ativo
        .groupby(["trimestre", "mes"])
        .agg(
            receita_media=("receita_liquida", "mean"),
            receita_total=("receita_liquida", "sum"),
            num_transacoes=("id_venda", "count"),
        )
        .reset_index()
        .sort_values("mes")
        .round(2)
    )


def analise_por_canal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compara desempenho entre loja física e e-commerce.

    Args:
        df: Tabela fato_vendas.

    Returns:
        DataFrame com métricas por canal de venda.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    resultado = (
        df_ativo
        .groupby("canal_venda")
        .agg(
            receita_liquida=("receita_liquida", "sum"),
            lucro_bruto=("lucro_bruto", "sum"),
            num_transacoes=("id_venda", "count"),
            ticket_medio=("receita_liquida", "mean"),
        )
        .reset_index()
    )

    resultado["margem_pct"] = (
        resultado["lucro_bruto"] / resultado["receita_liquida"] * 100
    ).round(2)

    resultado["participacao_receita_pct"] = (
        resultado["receita_liquida"] / resultado["receita_liquida"].sum() * 100
    ).round(2)

    return resultado.round(2)


def gerar_resumo_executivo(df: pd.DataFrame) -> None:
    """
    Imprime um resumo executivo formatado para apresentação à diretoria.

    Pensado para o Sr. Almir (fundador) que prefere números claros e
    objetivos, sem jargões técnicos.

    Args:
        df: Tabela fato_vendas.
    """
    kpis = faturamento_total(df)
    ticket = ticket_medio(df)

    separador = "=" * 55

    print(f"\n{separador}")
    print("  RESUMO EXECUTIVO — LH Nautical")
    print(separador)
    print(f"  Receita Total (líquida): R$ {kpis['receita_liquida']:>12,.2f}")
    print(f"  Lucro Bruto:             R$ {kpis['lucro_bruto']:>12,.2f}")
    print(f"  Margem Média:            {kpis['margem_media_pct']:>11.1f}%")
    print(f"  Total de Pedidos:        {kpis['total_transacoes']:>12,}")
    print(f"  Itens Vendidos:          {kpis['total_itens']:>12,}")
    print(f"  Ticket Médio/Pedido:     R$ {ticket['ticket_medio_transacao']:>12,.2f}")
    print(f"  Ticket Médio/Cliente:    R$ {ticket['ticket_medio_cliente']:>12,.2f}")
    print(separador + "\n")
