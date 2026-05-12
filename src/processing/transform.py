"""
Módulo de Transformação — LH Nautical
======================================
Pipeline Bronze → Silver → Gold adaptado ao schema real dos dados.

Problemas de qualidade identificados e tratados:
  vendas   : datas em dois formatos (YYYY-MM-DD e DD-MM-YYYY)
  produtos : preço como string 'R$ 33.122,52', categoria em maiúsculas
  clientes : localização com múltiplos separadores (,  /  -)
  custos   : histórico de preços USD aninhado em lista por produto

Decisões de modelagem:
  - status_venda  = 'concluida' (dados só contêm vendas efetivadas)
  - canal_venda   = 'loja_fisica' se cliente em SC, 'ecommerce' caso contrário
  - desconto_pct  = 0 (não disponível na fonte)
  - receita_liquida = receita_bruta (sem desconto)
  - custo_unitario  = preço USD mais recente × taxa de câmbio média do período
  - taxa_cambio_brl = R$ 5.10/USD (média 2023-2024)
"""

import re
import logging
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
SILVER_DIR = _PROJECT_ROOT / "data" / "silver"
GOLD_DIR   = _PROJECT_ROOT / "data" / "gold"

# Taxa de câmbio média BRL/USD para 2023-2024
TAXA_CAMBIO_BRL = 5.10

# Conjunto de siglas de estados brasileiros para o parser de localização
_ESTADOS_BR = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _parse_sale_date(val) -> pd.Timestamp:
    """
    Converte string de data para Timestamp, suportando dois formatos:
      - YYYY-MM-DD  (ISO 8601 — sistema do e-commerce)
      - DD-MM-YYYY  (padrão brasileiro — sistema da loja física)

    A distinção é feita pelo comprimento do primeiro segmento ao separar por '-'.
    """
    if pd.isna(val):
        return pd.NaT
    s = str(val).strip()
    parts = s.split("-")
    if len(parts) != 3:
        return pd.NaT
    try:
        if len(parts[0]) == 4:               # YYYY-MM-DD
            return pd.Timestamp(s)
        else:                                 # DD-MM-YYYY
            return pd.to_datetime(s, format="%d-%m-%Y")
    except Exception:
        return pd.NaT


def _clean_price(val) -> float:
    """
    Converte string de preço para float.
    Exemplos aceitos: 'R$ 33.122,52'  →  33122.52
                      'R$ 1890.00'    →  1890.00
                      1890.0          →  1890.0
    """
    if pd.isna(val):
        return np.nan
    s = str(val).replace("R$", "").strip()
    # Detecta separador decimal: se houver vírgula após ponto, é formato pt-BR
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    s = s.replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


def _parse_location(loc) -> Tuple[str, str]:
    """
    Extrai cidade e estado de strings de localização inconsistentes.

    Separadores suportados: vírgula, barra, hífen com espaços.
    A sigla do estado (2 letras maiúsculas) é identificada pelo conjunto _ESTADOS_BR;
    o restante é tratado como nome da cidade.

    Exemplos:
      'Aratu (Candeias) , BA'  →  ('Aratu (Candeias)', 'BA')
      'PE , Recife'            →  ('Recife', 'PE')
      'PB/Cabedelo'            →  ('Cabedelo', 'PB')
      'SE - Aracaju'           →  ('Aracaju', 'SE')
    """
    if pd.isna(loc):
        return "Desconhecida", "NA"

    loc_str = str(loc).strip()

    # Normaliza múltiplos separadores para '|'
    loc_str = re.sub(r"\s*/\s*|\s+-\s+|\s*,\s*", "|", loc_str)
    parts = [p.strip() for p in loc_str.split("|") if p.strip()]

    state = "NA"
    city_parts = []
    for part in parts:
        if part.upper() in _ESTADOS_BR:
            state = part.upper()
        else:
            city_parts.append(part)

    city = ", ".join(city_parts) if city_parts else "Desconhecida"
    return city, state


def _get_latest_usd_price(historic_data) -> float:
    """
    Retorna o preço USD mais recente de um produto a partir do histórico.

    O histórico é uma lista de dicts com 'start_date' (DD/MM/YYYY) e 'usd_price'.
    Ordena por data e retorna o último valor.
    """
    if not isinstance(historic_data, list) or len(historic_data) == 0:
        return np.nan

    entries = []
    for entry in historic_data:
        try:
            dt = pd.to_datetime(entry["start_date"], format="%d/%m/%Y", errors="coerce")
            entries.append((dt, float(entry["usd_price"])))
        except Exception:
            continue

    if not entries:
        return np.nan

    entries.sort(key=lambda x: x[0])
    return entries[-1][1]   # preço USD da entrada mais recente


def _normalize_category(cat) -> str:
    """
    Normaliza nomes de categoria para as 3 formas canônicas.

    O dataset contém 38 variações ortográficas para apenas 3 categorias:
      Eletrônicos, Propulsão, Ancoragem

    Estratégia:
    1. Remove espaços entre letras individuais ('E L E T R' → 'ELETR')
    2. Remove acentos e converte para lowercase
    3. Detecta prefixo característico de cada categoria
    """
    import unicodedata

    if pd.isna(cat):
        return "Outros"

    s = str(cat).strip()

    # Remove espaços entre letras isoladas ("E L E T R Ô N I C O S" → "ELETRÔNICOS")
    parts = s.split()
    if len(parts) > 2 and all(len(p) <= 2 for p in parts):
        s = "".join(parts)

    # Normaliza: remove acentos + minúsculas para comparação robusta
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower()

    if "eletr" in sem_acento:
        return "Eletrônicos"
    if "propu" in sem_acento or sem_acento.startswith("prop"):
        return "Propulsão"
    if "ancor" in sem_acento or "encor" in sem_acento:
        return "Ancoragem"

    return s.strip().title()


def _validar_email(email: str) -> bool:
    """Verifica formato mínimo de e-mail."""
    if pd.isna(email):
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email).strip()))


# ---------------------------------------------------------------------------
# Bronze → Silver
# ---------------------------------------------------------------------------

def clean_vendas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame de vendas (Bronze → Silver).

    Transformações:
    - Renomeia colunas para o padrão do projeto (PT-BR, snake_case)
    - Converte datas com dois formatos distintos
    - Remove duplicatas de id_venda
    - Adiciona colunas temporais derivadas
    - Adiciona status_venda='concluida' e desconto_pct=0 (ausentes na fonte)
    """
    df = df.copy()

    df = df.rename(columns={
        "id":         "id_venda",
        "id_client":  "id_cliente",
        "id_product": "id_produto",
        "qtd":        "quantidade",
        "total":      "receita_bruta",
        "sale_date":  "data_venda",
    })

    # Datas com dois formatos (YYYY-MM-DD e DD-MM-YYYY)
    df["data_venda"] = df["data_venda"].apply(_parse_sale_date)

    n_nulos = df["data_venda"].isna().sum()
    if n_nulos:
        logger.warning("[Vendas] %d datas não parseadas → removidas", n_nulos)
    df = df.dropna(subset=["data_venda"])

    before = len(df)
    df = df.drop_duplicates(subset=["id_venda"])
    if len(df) < before:
        logger.warning("[Vendas] %d duplicata(s) de id_venda removida(s)", before - len(df))

    # Colunas ausentes na fonte — atribuímos valores canônicos
    df["status_venda"] = "concluida"
    df["desconto_pct"] = 0.0

    # Colunas temporais para análise sazonal
    df["ano"]        = df["data_venda"].dt.year
    df["mes"]        = df["data_venda"].dt.month
    df["trimestre"]  = df["data_venda"].dt.quarter
    df["dia_semana"] = df["data_venda"].dt.day_name()

    logger.info("[Silver] Vendas: %d linhas", len(df))
    return df


def clean_produtos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame de produtos (Bronze → Silver).

    Transformações:
    - Renomeia colunas
    - Converte preço de string ('R$ 1.890,00') para float
    - Normaliza categoria para Title Case
    """
    df = df.copy()

    df = df.rename(columns={
        "code":             "id_produto",
        "name":             "nome_produto",
        "price":            "preco_venda",
        "actual_category":  "categoria",
    })

    df["preco_venda"]  = df["preco_venda"].apply(_clean_price)
    df["nome_produto"] = df["nome_produto"].str.strip()

    # Normaliza as 38 variações ortográficas para 3 categorias canônicas
    df["categoria"] = df["categoria"].apply(_normalize_category)

    # Remove duplicatas de produto — mesmo código com categoria inconsistente
    antes = len(df)
    df = df.drop_duplicates(subset=["id_produto"], keep="first")
    removidas = antes - len(df)
    if removidas:
        logger.warning("[Produtos] %d linha(s) duplicada(s) removida(s) (mesmo id_produto)", removidas)

    logger.info("[Silver] Produtos: %d linhas | Categorias: %s",
                len(df), df["categoria"].unique().tolist())
    return df


def clean_clientes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame de clientes (Bronze → Silver).

    Transformações:
    - Renomeia colunas
    - Extrai cidade e estado do campo 'location' (múltiplos separadores)
    - Valida e-mail (flag — não descarta registros inválidos)
    """
    df = df.copy()

    df = df.rename(columns={
        "code":       "id_cliente",
        "full_name":  "nome_completo",
        "location":   "localizacao_raw",
        "email":      "email",
    })

    parsed = df["localizacao_raw"].apply(_parse_location)
    df["cidade"] = [p[0] for p in parsed]
    df["estado"] = [p[1] for p in parsed]

    df["email_valido"] = df["email"].apply(_validar_email)
    invalidos = (~df["email_valido"]).sum()
    if invalidos:
        logger.warning("[Clientes] %d e-mail(s) inválido(s)", invalidos)

    df["nome_completo"] = df["nome_completo"].str.strip().str.title()

    logger.info("[Silver] Clientes: %d linhas", len(df))
    return df


def clean_custos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza o DataFrame de custos (Bronze → Silver).

    Transforma o histórico aninhado em uma coluna única por produto:
    - Extrai o preço USD mais recente de cada produto
    - Converte para BRL usando a taxa de câmbio média do período

    O custo em BRL representa o último preço de aquisição do produto,
    utilizado para calcular a margem de cada venda.
    """
    df = df.copy()

    df = df.rename(columns={"product_id": "id_produto"})

    df["custo_unitario_usd"] = df["historic_data"].apply(_get_latest_usd_price)
    df["custo_unitario_brl"] = (df["custo_unitario_usd"] * TAXA_CAMBIO_BRL).round(2)

    df = df[["id_produto", "custo_unitario_usd", "custo_unitario_brl"]].copy()

    sem_custo = df["custo_unitario_brl"].isna().sum()
    if sem_custo:
        logger.warning("[Custos] %d produto(s) sem custo histórico", sem_custo)

    logger.info("[Silver] Custos: %d linhas (taxa câmbio: R$ %.2f/USD)", len(df), TAXA_CAMBIO_BRL)
    return df


def save_to_silver(df: pd.DataFrame, name: str) -> Path:
    """Salva DataFrame na camada Silver (formato Parquet)."""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    path = SILVER_DIR / f"{name}.parquet"
    df.to_parquet(path, index=False, engine="pyarrow")
    logger.info("[Silver] Salvo: %s (%d linhas)", path.name, len(df))
    return path


# ---------------------------------------------------------------------------
# Silver → Gold
# ---------------------------------------------------------------------------

def build_silver_vendas(
    vendas: pd.DataFrame,
    produtos: pd.DataFrame,
    clientes: pd.DataFrame,
    custos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Enriquece vendas com produto, cliente e custo; calcula métricas financeiras.

    Joins:
      vendas ← produtos  (nome_produto, categoria, preco_venda)
      vendas ← clientes  (estado do cliente → canal_venda derivado)
      vendas ← custos    (custo_unitario_brl → custo_total)

    Métricas calculadas:
      receita_bruta   = total da venda (direto da fonte)
      desconto_valor  = 0  (sem dados de desconto)
      receita_liquida = receita_bruta  (= bruta pois desconto=0)
      custo_total     = quantidade × custo_unitario_brl
      lucro_bruto     = receita_liquida − custo_total
      margem_pct      = lucro_bruto / receita_liquida × 100

    Canal de venda derivado:
      estado SC → 'loja_fisica'  (mercado de proximidade da sede)
      demais   → 'ecommerce'     (vendas nacionais via site)
    """
    # Seleciona apenas o necessário de cada dimensão para o join
    prod_join = produtos[["id_produto", "nome_produto", "categoria", "preco_venda"]]
    cli_join  = clientes[["id_cliente", "estado"]]

    df = (
        vendas
        .merge(prod_join, on="id_produto", how="left")
        .merge(cli_join,  on="id_cliente", how="left")
        .merge(custos,    on="id_produto", how="left")
    )

    # Canal derivado do estado do cliente
    df["canal_venda"] = df["estado"].apply(
        lambda uf: "loja_fisica" if str(uf).upper() == "SC" else "ecommerce"
    )

    # Métricas financeiras
    df["desconto_valor"]  = 0.0
    df["receita_liquida"] = df["receita_bruta"].round(2)
    df["custo_total"]     = (df["quantidade"] * df["custo_unitario_brl"]).round(2)
    df["lucro_bruto"]     = (df["receita_liquida"] - df["custo_total"]).round(2)
    df["margem_pct"]      = (
        df["lucro_bruto"] / df["receita_liquida"].replace(0, np.nan) * 100
    ).round(2)

    prejuizo = (df["lucro_bruto"] < 0).sum()
    if prejuizo:
        logger.warning("[Silver+] %d transações com margem negativa (revisar custo)", prejuizo)

    logger.info("[Silver+] Vendas enriquecidas: %d linhas, %d colunas", *df.shape)
    return df


def build_gold_fato_vendas(df_silver: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói a tabela fato_vendas para o modelo estrela (Gold).

    Seleciona apenas colunas métricas e chaves, sem atributos descritivos
    (que ficam nas dimensões), seguindo o padrão Kimball.
    """
    cols = [
        "id_venda", "data_venda", "id_cliente", "id_produto",
        "canal_venda", "status_venda",
        "quantidade", "receita_bruta", "desconto_pct", "desconto_valor",
        "receita_liquida", "custo_total", "lucro_bruto", "margem_pct",
        "ano", "mes", "trimestre", "dia_semana",
    ]
    fato = df_silver[[c for c in cols if c in df_silver.columns]].copy()
    logger.info("[Gold] fato_vendas: %d linhas × %d colunas", *fato.shape)
    return fato


def build_gold_dims(
    clientes: pd.DataFrame,
    produtos: pd.DataFrame,
    custos: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """
    Constrói as tabelas dimensão do modelo estrela (Gold).

    dim_clientes: dados cadastrais com cidade/estado parseados
    dim_produtos: catálogo com preço de venda e custo em BRL
    """
    dim_clientes = clientes[[
        "id_cliente", "nome_completo", "email", "email_valido",
        "cidade", "estado",
    ]].copy()

    dim_produtos = (
        produtos[["id_produto", "nome_produto", "categoria", "preco_venda"]]
        .merge(custos[["id_produto", "custo_unitario_brl"]], on="id_produto", how="left")
    )
    dim_produtos["margem_unitaria_pct"] = (
        (dim_produtos["preco_venda"] - dim_produtos["custo_unitario_brl"])
        / dim_produtos["preco_venda"] * 100
    ).round(2)

    dims = {"dim_clientes": dim_clientes, "dim_produtos": dim_produtos}
    for nome, df in dims.items():
        logger.info("[Gold] %s: %d linhas", nome, len(df))
    return dims


def save_to_gold(df: pd.DataFrame, name: str) -> Path:
    """Salva DataFrame na camada Gold (formato Parquet)."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    path = GOLD_DIR / f"{name}.parquet"
    df.to_parquet(path, index=False, engine="pyarrow")
    logger.info("[Gold] Salvo: %s (%d linhas)", path.name, len(df))
    return path


def run_transformation_pipeline(
    datasets: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    """
    Executa o pipeline completo Bronze → Silver → Gold.

    Args:
        datasets: saída de load_all_raw_data()

    Returns:
        Dicionário com todas as tabelas Gold prontas para análise.
    """
    logger.info("=" * 55)
    logger.info("PIPELINE DE TRANSFORMAÇÃO — LH Nautical")
    logger.info("=" * 55)

    # --- Bronze → Silver ---
    silver_vendas   = clean_vendas(datasets["vendas"])
    silver_produtos = clean_produtos(datasets["produtos"])
    silver_clientes = clean_clientes(datasets["clientes"])
    silver_custos   = clean_custos(datasets["custos"])

    for nome, df in [
        ("vendas", silver_vendas), ("produtos", silver_produtos),
        ("clientes", silver_clientes), ("custos", silver_custos),
    ]:
        save_to_silver(df, nome)

    # --- Silver → Gold ---
    silver_rich = build_silver_vendas(
        silver_vendas, silver_produtos, silver_clientes, silver_custos
    )
    fato  = build_gold_fato_vendas(silver_rich)
    dims  = build_gold_dims(silver_clientes, silver_produtos, silver_custos)

    save_to_gold(fato, "fato_vendas")
    for nome, df in dims.items():
        save_to_gold(df, nome)

    logger.info("PIPELINE CONCLUÍDO — Gold pronto para análise")

    return {"fato_vendas": fato, **dims}
