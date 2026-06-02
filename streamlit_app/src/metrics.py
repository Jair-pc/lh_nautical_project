import pandas as pd

STATUS_OK  = "concluida"
STATUS_CAN = "cancelada"
STATUS_DEV = "devolvida"

_DIA_ORDEM = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


# ── helpers ────────────────────────────────────────────────────────────────────

def ok(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status_venda"] == STATUS_OK]


def fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── KPIs escalares ─────────────────────────────────────────────────────────────

def receita_liquida_total(df: pd.DataFrame) -> float:
    return ok(df)["receita_liquida"].sum()

def receita_bruta_total(df: pd.DataFrame) -> float:
    return ok(df)["receita_bruta"].sum()

def lucro_bruto_total(df: pd.DataFrame) -> float:
    return ok(df)["lucro_bruto"].sum()

def custo_total(df: pd.DataFrame) -> float:
    return ok(df)["custo_total"].sum()

def margem_pct(df: pd.DataFrame) -> float:
    rec = receita_liquida_total(df)
    return (lucro_bruto_total(df) / rec * 100) if rec else 0.0

def ticket_medio(df: pd.DataFrame) -> float:
    conc = ok(df)
    return conc["receita_liquida"].mean() if not conc.empty else 0.0

def total_pedidos(df: pd.DataFrame) -> int:
    return ok(df)["id_venda"].nunique()

def quantidade_total(df: pd.DataFrame) -> int:
    return int(ok(df)["quantidade"].sum())

def total_clientes_unicos(df: pd.DataFrame) -> int:
    return ok(df)["id_cliente"].nunique()

def receita_por_cliente(df: pd.DataFrame) -> float:
    n = total_clientes_unicos(df)
    return receita_liquida_total(df) / n if n else 0.0

def pedidos_por_cliente(df: pd.DataFrame) -> float:
    n = total_clientes_unicos(df)
    return total_pedidos(df) / n if n else 0.0


# ── cancelamentos / devoluções ─────────────────────────────────────────────────

def stats_cancelamentos(df: pd.DataFrame) -> dict:
    can = df[df["status_venda"] == STATUS_CAN]
    dev = df[df["status_venda"] == STATUS_DEV]
    total_todos = df["id_venda"].nunique() or 1
    return {
        "n_cancelados":      can["id_venda"].nunique(),
        "receita_cancelada": can["receita_liquida"].sum(),
        "taxa_cancel_pct":   can["id_venda"].nunique() / total_todos * 100,
        "n_devolvidos":      dev["id_venda"].nunique(),
        "receita_devolvida": dev["receita_liquida"].sum(),
    }


# ── séries / agrupamentos ──────────────────────────────────────────────────────

def receita_mensal(df: pd.DataFrame) -> pd.DataFrame:
    return (ok(df)
            .groupby(["ano", "mes", "mes_nome", "ano_mes"])
            .agg(receita=("receita_liquida", "sum"),
                 lucro=("lucro_bruto", "sum"),
                 pedidos=("id_venda", "nunique"),
                 qtd=("quantidade", "sum"))
            .reset_index()
            .sort_values("ano_mes"))

def receita_por_canal(df: pd.DataFrame) -> pd.DataFrame:
    r = (ok(df)
         .groupby("canal_venda")
         .agg(receita=("receita_liquida", "sum"),
              pedidos=("id_venda", "nunique"))
         .reset_index()
         .sort_values("receita", ascending=False))
    total = r["receita"].sum() or 1
    r["share_pct"] = (r["receita"] / total * 100).round(1)
    return r

def receita_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    r = (ok(df)
         .groupby("categoria")
         .agg(receita=("receita_liquida", "sum"),
              lucro=("lucro_bruto", "sum"),
              qtd=("quantidade", "sum"))
         .reset_index()
         .sort_values("receita", ascending=False))
    r["margem_pct"] = (r["lucro"] / r["receita"].replace(0, float("nan")) * 100).round(1)
    return r

def top_produtos(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    r = (ok(df)
         .groupby(["id_produto", "nome_produto", "categoria"])
         .agg(receita=("receita_liquida", "sum"),
              lucro=("lucro_bruto", "sum"),
              qtd=("quantidade", "sum"),
              pedidos=("id_venda", "nunique"))
         .reset_index()
         .sort_values("receita", ascending=False)
         .head(n))
    r["margem_pct"] = (r["lucro"] / r["receita"].replace(0, float("nan")) * 100).round(1)
    return r

def top_clientes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (ok(df)
            .groupby(["id_cliente", "nome_completo", "estado", "cidade"])
            .agg(receita=("receita_liquida", "sum"),
                 pedidos=("id_venda", "nunique"),
                 qtd=("quantidade", "sum"))
            .reset_index()
            .sort_values("receita", ascending=False)
            .head(n))

def margem_por_produto(df: pd.DataFrame) -> pd.DataFrame:
    conc = ok(df)
    r = (conc.groupby(["id_produto", "nome_produto", "categoria"])
         .agg(receita=("receita_liquida", "sum"),
              lucro=("lucro_bruto", "sum"),
              qtd=("quantidade", "sum"))
         .reset_index())
    r["margem_pct"] = (r["lucro"] / r["receita"].replace(0, float("nan")) * 100).round(2)
    return r.sort_values("margem_pct")

def receita_por_estado(df: pd.DataFrame) -> pd.DataFrame:
    return (ok(df)
            .groupby("estado")
            .agg(receita=("receita_liquida", "sum"),
                 clientes=("id_cliente", "nunique"))
            .reset_index()
            .sort_values("receita", ascending=False))

def segmentacao_clientes(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa receita por estado (substituto ao segmento ausente nos dados)."""
    return (ok(df)
            .groupby("estado")
            .agg(receita=("receita_liquida", "sum"),
                 clientes=("id_cliente", "nunique"),
                 pedidos=("id_venda", "nunique"))
            .reset_index()
            .sort_values("receita", ascending=False)
            .head(8))

def vendas_por_dia_semana(df: pd.DataFrame) -> pd.DataFrame:
    r = (ok(df)
         .groupby("dia_semana")
         .agg(receita=("receita_liquida", "sum"),
              pedidos=("id_venda", "nunique"))
         .reset_index())
    r["dia_semana"] = pd.Categorical(r["dia_semana"], categories=_DIA_ORDEM, ordered=True)
    return r.sort_values("dia_semana").reset_index(drop=True)

def heatmap_mes_ano(df: pd.DataFrame) -> pd.DataFrame:
    pivot = (ok(df)
             .groupby(["ano", "mes"])["receita_liquida"]
             .sum()
             .unstack(level=0)
             .fillna(0))
    return pivot
