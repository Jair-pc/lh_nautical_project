import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.data_loader import load_all
from src.filters import setup_page, sidebar_brand, kpi_card, insight, section
from src.metrics import ok, fmt_brl
from src.recommendation import (
    produtos_mais_populares, produtos_relacionados,
    produtos_comprados_juntos, ranking_popularidade,
)
from src.charts import chart_popularidade

setup_page("Recomendações", "Popularidade, produtos relacionados e padrões de compra conjunta", "🤖")

df, *_ = load_all()
sidebar_brand()

# ── KPIs rápidos ──────────────────────────────────────────────────────────────
section("Resumo do Catálogo")
conc = ok(df)
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(kpi_card("Produtos Vendidos", str(conc["id_produto"].nunique()),
                         color="primary"), unsafe_allow_html=True)
with k2:
    top1 = conc.groupby("nome_produto")["quantidade"].sum().idxmax() if not conc.empty else "–"
    st.markdown(kpi_card("Produto #1 Popularidade", top1, color="success"), unsafe_allow_html=True)
with k3:
    n_cat = conc["categoria"].nunique() if "categoria" in conc.columns else 0
    st.markdown(kpi_card("Categorias Ativas", str(n_cat), color="neutral"), unsafe_allow_html=True)

st.space("small")

# ── top 10 popularidade ────────────────────────────────────────────────────────
section("Produtos Mais Vendidos (por Quantidade)")
df_pop = produtos_mais_populares(df, n=10)
if not df_pop.empty:
    st.plotly_chart(chart_popularidade(df_pop, height=420))

# ── produtos relacionados ──────────────────────────────────────────────────────
section("Produtos Relacionados por Categoria")
col_sel, col_res = st.columns([1, 2])

produtos_disponiveis = (conc[["id_produto", "nome_produto"]]
                        .drop_duplicates()
                        .sort_values("nome_produto"))

with col_sel:
    opts = dict(zip(produtos_disponiveis["nome_produto"], produtos_disponiveis["id_produto"]))
    escolhido_nome = st.selectbox("Selecione um produto:", list(opts.keys()))
    escolhido_id   = opts[escolhido_nome]

with col_res:
    relacionados = produtos_relacionados(df, escolhido_id, n=6)
    if not relacionados.empty:
        st.markdown(f"**Produtos relacionados a:** {escolhido_nome}")
        st.dataframe(
            relacionados.rename(columns={
                "nome_produto": "Produto",
                "qtd":          "Qtd Vendida",
                "receita":      "Receita (R$)",
            })
            .style.format({"Receita (R$)": "{:,.2f}"}),
            )
    else:
        st.caption("Nenhum produto relacionado encontrado para este item.")

# ── comprados juntos ──────────────────────────────────────────────────────────
section("Produtos Frequentemente Comprados Juntos (por Cliente)")
df_juntos = produtos_comprados_juntos(df, min_support=2)

if not df_juntos.empty:
    insight(
        "Market Basket Analysis (simplificado)",
        "Identifica pares de produtos adquiridos pelo mesmo cliente ao longo do tempo. "
        "Frequência ≥ 2 clientes distintos é o filtro mínimo aplicado."
    )
    st.dataframe(
        df_juntos.rename(columns={
            "produto_a":  "Produto A",
            "produto_b":  "Produto B",
            "frequencia": "Frequência (clientes)",
        }),
        height=300,
    )
else:
    st.caption("Nenhum par de produtos com co-ocorrência suficiente. Tente reduzir o filtro de suporte mínimo.")

# ── ranking completo ───────────────────────────────────────────────────────────
with st.expander("📋 Ranking completo de popularidade"):
    df_rank = ranking_popularidade(df)
    st.dataframe(
        df_rank[["rank", "nome_produto", "categoria", "qtd", "receita", "clientes", "share_qtd"]]
        .rename(columns={
            "rank":         "#",
            "nome_produto": "Produto",
            "categoria":    "Categoria",
            "qtd":          "Qtd Total",
            "receita":      "Receita (R$)",
            "clientes":     "Clientes",
            "share_qtd":    "Share Qtd (%)",
        })
        .style.format({"Receita (R$)": "{:,.2f}", "Share Qtd (%)": "{:.1f}"}),
        height=420,
    )
