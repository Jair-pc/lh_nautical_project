import pandas as pd
from pathlib import Path
import streamlit as st

GOLD_PATH = Path(__file__).parent.parent.parent / "data" / "gold"

_MES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}
_DIA_PT = {
    "Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta",
    "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo",
}
_DIA_ORDEM = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


@st.cache_data(max_entries=1)
def load_fato_vendas() -> pd.DataFrame:
    df = pd.read_parquet(GOLD_PATH / "fato_vendas.parquet")
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    # ano, mes, trimestre, dia_semana já existem no parquet
    df["mes_nome"]   = df["mes"].map(_MES_PT)
    df["ano_mes"]    = df["data_venda"].dt.to_period("M").astype(str)
    df["dia_semana"] = df["dia_semana"].map(_DIA_PT)   # traduz EN → PT
    # normalização defensiva
    df["status_venda"] = df["status_venda"].str.lower().str.strip()
    df["canal_venda"]  = df["canal_venda"].str.strip()
    return df


@st.cache_data(max_entries=1)
def load_dim_clientes() -> pd.DataFrame:
    return pd.read_parquet(GOLD_PATH / "dim_clientes.parquet")


@st.cache_data(max_entries=1)
def load_dim_produtos() -> pd.DataFrame:
    return pd.read_parquet(GOLD_PATH / "dim_produtos.parquet")


@st.cache_data(max_entries=1)
def load_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fato     = load_fato_vendas()
    clientes = load_dim_clientes()
    produtos = load_dim_produtos()
    df = (fato
          .merge(clientes, on="id_cliente", how="left")
          .merge(produtos,  on="id_produto",  how="left"))
    return df, fato, clientes, produtos
