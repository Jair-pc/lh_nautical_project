"""Módulo de Análise: métricas de vendas, clientes e produtos."""
from .sales_analysis import (
    faturamento_total,
    faturamento_mensal,
    ticket_medio,
    margem_por_produto,
    vendas_por_dia_semana,
    analise_sazonalidade,
    ranking_produtos,
    ranking_clientes,
    analise_por_canal,
)

__all__ = [
    "faturamento_total", "faturamento_mensal", "ticket_medio",
    "margem_por_produto", "vendas_por_dia_semana", "analise_sazonalidade",
    "ranking_produtos", "ranking_clientes", "analise_por_canal",
]
