"""Módulo de Ingestão: carrega dados brutos e salva na camada Bronze."""
from .ingest import load_all_raw_data, load_csv, load_json

__all__ = ["load_all_raw_data", "load_csv", "load_json"]
