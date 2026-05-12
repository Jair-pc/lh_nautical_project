"""
Módulo de Recomendação de Produtos — LH Nautical
=================================================
Implementa três abordagens complementares de recomendação:

  1. Popularidade global     — produtos mais vendidos (cold start)
  2. Produtos relacionados   — co-ocorrência em transações do mesmo cliente
  3. Análise de cesta (MBA)  — pares de produtos frequentemente comprados juntos

Todas as abordagens são não-personalizadas no nível de usuário individual
(filtro colaborativo requer maior volume de dados). O foco é em
recomendações de catálogo úteis para:
  - Página de produto no e-commerce ("Clientes também compraram")
  - Sugestões de venda cruzada na loja física
  - Montagem de kits promocionais
"""

import logging
from itertools import combinations
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def recomendacao_por_popularidade(
    df: pd.DataFrame,
    n: int = 10,
    por: str = "receita",
) -> pd.DataFrame:
    """
    Retorna os N produtos mais populares do catálogo.

    É a recomendação mais simples e eficaz para novos usuários
    (problema de cold start), funcionando bem quando não há
    histórico individual do cliente.

    Args:
        df:  Tabela fato_vendas (Gold).
        n:   Número de produtos a retornar.
        por: Critério de popularidade: 'receita' | 'volume' | 'frequencia'.

    Returns:
        DataFrame com os N produtos mais populares e suas métricas.
    """
    criterios = {
        "receita":   "receita_liquida",
        "volume":    "quantidade",
        "frequencia": "id_venda",
    }

    if por not in criterios:
        raise ValueError(f"Critério inválido: {por}. Opções: {list(criterios)}")

    df_ativo = df[df["status_venda"] == "concluida"]
    col = criterios[por]

    agg_func = "count" if por == "frequencia" else "sum"
    resultado = (
        df_ativo
        .groupby("id_produto")
        .agg(
            score=(col, agg_func),
            receita_total=("receita_liquida", "sum"),
            clientes_unicos=("id_cliente", "nunique"),
        )
        .reset_index()
        .sort_values("score", ascending=False)
        .head(n)
    )

    resultado["rank"] = range(1, len(resultado) + 1)
    resultado = resultado.rename(columns={"score": f"score_{por}"})

    logger.info("[Recomendação] Top %d por %s gerado", n, por)
    return resultado.round(2)


def produtos_relacionados(
    df: pd.DataFrame,
    produto_id: str,
    n: int = 5,
    min_clientes_comuns: int = 1,
) -> pd.DataFrame:
    """
    Retorna produtos frequentemente comprados pelo mesmo cliente
    que comprou `produto_id`.

    Lógica: identifica clientes que compraram o produto-alvo e
    verifica quais outros produtos esses mesmos clientes compraram.
    Produtos com mais clientes em comum = mais relacionados.

    Args:
        df:                   Tabela fato_vendas.
        produto_id:           ID do produto-alvo (ex.: 'P010').
        n:                    Número de recomendações a retornar.
        min_clientes_comuns:  Mínimo de clientes em comum para incluir.

    Returns:
        DataFrame com produtos relacionados e número de clientes comuns.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    # Clientes que compraram o produto-alvo
    clientes_alvo = set(
        df_ativo[df_ativo["id_produto"] == produto_id]["id_cliente"]
    )

    if not clientes_alvo:
        logger.warning("[Recomendação] Produto %s sem histórico de compras", produto_id)
        return pd.DataFrame()

    # Outros produtos comprados por esses mesmos clientes
    compras_relacionadas = df_ativo[
        (df_ativo["id_cliente"].isin(clientes_alvo)) &
        (df_ativo["id_produto"] != produto_id)
    ]

    resultado = (
        compras_relacionadas
        .groupby("id_produto")
        .agg(
            clientes_comuns=("id_cliente", "nunique"),
            vezes_comprado=("id_venda", "count"),
        )
        .reset_index()
        .query(f"clientes_comuns >= {min_clientes_comuns}")
        .sort_values("clientes_comuns", ascending=False)
        .head(n)
    )

    logger.info(
        "[Recomendação] Produto %s → %d produtos relacionados encontrados",
        produto_id, len(resultado),
    )

    return resultado


def analise_cesta_compras(
    df: pd.DataFrame,
    min_suporte: int = 2,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Identifica pares de produtos comprados pelo mesmo cliente.

    Market Basket Analysis simplificada: conta quantos clientes
    distintos compraram cada par de produtos. Pares com alto
    suporte são candidatos a:
    - Kits promocionais ("Compre junto")
    - Recomendações "Clientes também compraram"
    - Cross-sell na loja física

    Args:
        df:           Tabela fato_vendas.
        min_suporte:  Número mínimo de clientes que compraram o par.
        top_n:        Número de pares a retornar.

    Returns:
        DataFrame com pares de produtos e métricas de suporte.
    """
    df_ativo = df[df["status_venda"] == "concluida"]

    # Agrupa produtos por cliente
    cestas = (
        df_ativo
        .groupby("id_cliente")["id_produto"]
        .apply(set)
    )

    # Gera todos os pares de produtos por cliente
    pares: dict = {}
    for produtos_cliente in cestas:
        if len(produtos_cliente) < 2:
            continue
        for par in combinations(sorted(produtos_cliente), 2):
            pares[par] = pares.get(par, 0) + 1

    if not pares:
        logger.warning("[MBA] Nenhum par encontrado com os dados disponíveis")
        return pd.DataFrame()

    resultado = (
        pd.DataFrame(
            [(p[0], p[1], cnt) for p, cnt in pares.items()],
            columns=["produto_a", "produto_b", "clientes_comuns"],
        )
        .query(f"clientes_comuns >= {min_suporte}")
        .sort_values("clientes_comuns", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    total_clientes = df_ativo["id_cliente"].nunique()
    resultado["suporte_pct"] = (resultado["clientes_comuns"] / total_clientes * 100).round(2)

    logger.info(
        "[MBA] %d pares encontrados (suporte mínimo: %d clientes)",
        len(resultado), min_suporte,
    )

    return resultado
