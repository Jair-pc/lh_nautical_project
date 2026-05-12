"""Módulo de Recomendação: produtos populares, relacionados e cesta de compras."""
from .recommender import (
    recomendacao_por_popularidade,
    produtos_relacionados,
    analise_cesta_compras,
)

__all__ = [
    "recomendacao_por_popularidade",
    "produtos_relacionados",
    "analise_cesta_compras",
]
