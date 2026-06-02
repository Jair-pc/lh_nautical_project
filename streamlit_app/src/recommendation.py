import pandas as pd
from itertools import combinations
from collections import Counter


def produtos_mais_populares(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    from src.metrics import ok
    r = (ok(df)
         .groupby(["id_produto", "nome_produto", "categoria"])
         .agg(qtd=("quantidade", "sum"),
              receita=("receita_liquida", "sum"),
              n_pedidos=("id_venda", "nunique"))
         .reset_index()
         .sort_values("qtd", ascending=False)
         .head(n))
    r["rank"] = range(1, len(r) + 1)
    return r


def produtos_relacionados(df: pd.DataFrame, produto_id: int, n: int = 5) -> pd.DataFrame:
    from src.metrics import ok
    conc = ok(df)

    if produto_id not in conc["id_produto"].values:
        return pd.DataFrame()

    cat = conc[conc["id_produto"] == produto_id]["categoria"].iloc[0]

    return (conc[
                (conc["categoria"] == cat) &
                (conc["id_produto"] != produto_id)
            ]
            .groupby(["id_produto", "nome_produto"])
            .agg(qtd=("quantidade", "sum"),
                 receita=("receita_liquida", "sum"))
            .reset_index()
            .sort_values("receita", ascending=False)
            .head(n))


def produtos_comprados_juntos(df: pd.DataFrame, min_support: int = 2) -> pd.DataFrame:
    from src.metrics import ok
    conc = ok(df)

    # agrupa produtos por cliente (proxy de "comprados juntos")
    cliente_produtos = (conc
                        .groupby("id_cliente")["id_produto"]
                        .apply(list)
                        .reset_index())

    par_count: Counter = Counter()
    for _, row in cliente_produtos.iterrows():
        produtos_unicos = list(set(row["id_produto"]))
        for par in combinations(sorted(produtos_unicos), 2):
            par_count[par] += 1

    if not par_count:
        return pd.DataFrame()

    # mapa id → nome
    nome_map = (conc[["id_produto", "nome_produto"]]
                .drop_duplicates()
                .set_index("id_produto")["nome_produto"]
                .to_dict())

    rows = []
    for (p1, p2), cnt in par_count.items():
        if cnt >= min_support:
            rows.append({
                "produto_a": nome_map.get(p1, str(p1)),
                "produto_b": nome_map.get(p2, str(p2)),
                "frequencia": cnt,
            })

    if not rows:
        return pd.DataFrame()

    return (pd.DataFrame(rows)
            .sort_values("frequencia", ascending=False)
            .reset_index(drop=True))


def ranking_popularidade(df: pd.DataFrame) -> pd.DataFrame:
    from src.metrics import ok
    conc = ok(df)
    total_qtd = conc["quantidade"].sum() or 1

    r = (conc
         .groupby(["id_produto", "nome_produto", "categoria"])
         .agg(qtd=("quantidade", "sum"),
              receita=("receita_liquida", "sum"),
              clientes=("id_cliente", "nunique"))
         .reset_index()
         .sort_values("qtd", ascending=False)
         .reset_index(drop=True))

    r["rank"]       = r.index + 1
    r["share_qtd"]  = (r["qtd"] / total_qtd * 100).round(1)
    return r
