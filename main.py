"""
LH Nautical — Pipeline Principal de Dados
==========================================
Orquestra todas as etapas do pipeline de dados, da ingestão
à geração de insights e recomendações.

Etapas executadas:
  1. Ingestão       RAW → Bronze
  2. Transformação  Bronze → Silver → Gold
  3. Análise        KPIs e relatório executivo
  4. Previsão       Demanda para os próximos meses
  5. Recomendação   Produtos populares e relacionados

Uso:
    python main.py
    python main.py --etapa ingestion
    python main.py --etapa analysis
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Adiciona o diretório do projeto ao Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.ingest import load_all_raw_data as run_ingestion_pipeline
from src.processing.transform import run_transformation_pipeline
from src.analysis.sales_analysis import (
    gerar_resumo_executivo,
    faturamento_mensal,
    margem_por_produto,
    analise_por_canal,
    vendas_por_dia_semana,
    produtos_com_prejuizo,
    ranking_clientes,
)
from src.forecasting.demand_forecast import gerar_relatorio_previsao
from src.recommendation.recommender import (
    recomendacao_por_popularidade,
    analise_cesta_compras,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(module)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _banner():
    print("=" * 57)
    print("  LH Nautical -- Pipeline de Dados")
    print("  Arquitetura Medallion: Bronze -> Silver -> Gold")
    print("=" * 57)


def run_ingestion():
    """Etapa 1: Carrega dados brutos e persiste na camada Bronze."""
    logger.info("▶ ETAPA 1 — Ingestão (RAW → Bronze)")
    return run_ingestion_pipeline()


def run_transformation(datasets):
    """Etapa 2: Limpa, transforma e cria as tabelas Gold."""
    logger.info("▶ ETAPA 2 — Transformação (Bronze → Silver → Gold)")
    return run_transformation_pipeline(datasets)


def run_analysis(gold_tables):
    """Etapa 3: Gera KPIs e relatório executivo."""
    logger.info("▶ ETAPA 3 — Análise de Negócio")

    fato = gold_tables["fato_vendas"]

    # Resumo executivo para a diretoria
    gerar_resumo_executivo(fato)

    # Faturamento mensal
    mensal = faturamento_mensal(fato)
    print("\n[Faturamento Mensal — últimos 5 períodos]")
    print(mensal.tail(5).to_string(index=False))

    # Análise por canal
    print("\n[Desempenho por Canal de Venda]")
    print(analise_por_canal(fato).to_string(index=False))

    # Dia da semana
    print("\n[Vendas por Dia da Semana]")
    print(vendas_por_dia_semana(fato)[["dia_semana_pt", "receita_liquida", "num_transacoes"]].to_string(index=False))

    # Margem por produto (top 5)
    print("\n[Top 5 Produtos por Receita]")
    print(margem_por_produto(fato, top_n=5).to_string(index=False))

    # Alertas: produtos com prejuízo
    prejuizo = produtos_com_prejuizo(fato)
    if not prejuizo.empty:
        print(f"\n[! ALERTA] {len(prejuizo)} produto(s) com margem negativa:")
        print(prejuizo.to_string(index=False))
    else:
        print("\n[OK] Nenhum produto com prejuizo acumulado detectado.")

    # Top clientes
    print("\n[Top 5 Clientes por Receita]")
    print(ranking_clientes(fato, top_n=5).to_string(index=False))


def run_forecasting(gold_tables):
    """Etapa 4: Gera previsão de demanda."""
    logger.info("▶ ETAPA 4 — Previsão de Demanda")
    gerar_relatorio_previsao(gold_tables["fato_vendas"])


def run_recommendation(gold_tables):
    """Etapa 5: Gera recomendações de produtos."""
    logger.info("▶ ETAPA 5 — Sistema de Recomendação")

    fato = gold_tables["fato_vendas"]

    print("\n[Top 10 Produtos por Popularidade (Receita)]")
    print(recomendacao_por_popularidade(fato, n=10).to_string(index=False))

    print("\n[Análise de Cesta — Pares mais comprados juntos]")
    cesta = analise_cesta_compras(fato, min_suporte=2, top_n=10)
    if not cesta.empty:
        print(cesta.to_string(index=False))
    else:
        print("  Volume de dados insuficiente para análise de cesta robusta.")
        print("  Recomenda-se reavaliar com histórico de 12+ meses e 500+ transações.")


def run_full_pipeline():
    """Executa todas as etapas sequencialmente."""
    _banner()
    t0 = time.time()

    datasets    = run_ingestion()
    gold_tables = run_transformation(datasets)
    run_analysis(gold_tables)
    run_forecasting(gold_tables)
    run_recommendation(gold_tables)

    elapsed = time.time() - t0
    print(f"\n{'='*55}")
    print(f"  Pipeline concluído em {elapsed:.2f}s")
    print(f"  Camadas salvas em: data/bronze | data/silver | data/gold")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LH Nautical — Pipeline de Dados")
    parser.add_argument(
        "--etapa",
        choices=["all", "ingestion", "transformation", "analysis", "forecast", "recommendation"],
        default="all",
        help="Etapa específica do pipeline a executar (padrão: all)",
    )
    args = parser.parse_args()

    if args.etapa == "all":
        run_full_pipeline()
    else:
        _banner()
        datasets = run_ingestion()
        gold_tables = run_transformation(datasets)

        etapas = {
            "ingestion":      lambda: None,
            "transformation": lambda: None,
            "analysis":       lambda: run_analysis(gold_tables),
            "forecast":       lambda: run_forecasting(gold_tables),
            "recommendation": lambda: run_recommendation(gold_tables),
        }
        etapas[args.etapa]()
