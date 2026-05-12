"""
Módulo de Ingestão de Dados — LH Nautical
==========================================
Lê os arquivos de origem da camada Bronze (CSV e JSON) e os disponibiliza
como DataFrames para o pipeline de transformação.

Neste projeto, os arquivos brutos já foram depositados diretamente em
data/bronze/ pelo time de operações. A camada Bronze portanto serve
como ponto de entrada, e o pipeline processa daqui para Silver e Gold.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(module)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Os dados de origem estão na camada Bronze (depositados pelo time de operações)
BRONZE_DIR = _PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = _PROJECT_ROOT / "data" / "silver"
GOLD_DIR   = _PROJECT_ROOT / "data" / "gold"


def load_csv(file_name: str, source_dir: Path = BRONZE_DIR, **kwargs) -> Optional[pd.DataFrame]:
    """Carrega um arquivo CSV do diretório de origem."""
    path = source_dir / file_name
    if not path.exists():
        logger.error("Arquivo não encontrado: %s", path)
        return None
    try:
        df = pd.read_csv(path, encoding="utf-8", **kwargs)
        logger.info("[Bronze] %s → %d linhas × %d colunas", file_name, *df.shape)
        return df
    except Exception as exc:
        logger.error("Falha ao carregar %s: %s", file_name, exc)
        return None


def load_json(file_name: str, source_dir: Path = BRONZE_DIR) -> Optional[pd.DataFrame]:
    """Carrega um arquivo JSON e normaliza em DataFrame."""
    path = source_dir / file_name
    if not path.exists():
        logger.error("Arquivo não encontrado: %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        df = pd.DataFrame(data if isinstance(data, list) else [data])
        logger.info("[Bronze] %s → %d linhas × %d colunas", file_name, *df.shape)
        return df
    except Exception as exc:
        logger.error("Falha ao carregar %s: %s", file_name, exc)
        return None


def load_all_raw_data() -> Dict[str, pd.DataFrame]:
    """
    Carrega todos os arquivos Bronze do projeto LH Nautical.

    Returns:
        Dicionário com as chaves:
        - 'vendas'   → transações 2023-2024 (9.895 linhas)
        - 'produtos' → catálogo com preços em BRL
        - 'clientes' → base CRM com localização
        - 'custos'   → histórico de custos em USD por produto
    """
    logger.info("=" * 55)
    logger.info("INGESTÃO — LH Nautical | Fonte: data/bronze/")
    logger.info("=" * 55)

    datasets = {
        "vendas":   load_csv("vendas_2023_2024.csv"),
        "produtos": load_csv("produtos_raw.csv"),
        "clientes": load_json("clientes_crm.json"),
        "custos":   load_json("custos_importacao.json"),
    }

    ok     = [k for k, v in datasets.items() if v is not None]
    failed = [k for k, v in datasets.items() if v is None]

    if failed:
        logger.warning("Datasets com falha: %s", failed)
    logger.info("Carregados: %s | INGESTÃO CONCLUÍDA", ok)

    return {k: v for k, v in datasets.items() if v is not None}
