import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.data_loader import load_all
from src.filters import setup_page, sidebar_filters, kpi_card, insight, section
from src.metrics import (
    top_produtos, receita_por_categoria, margem_por_produto,
    receita_liquida_total, margem_pct, fmt_brl,
)
from src.charts import (
    chart_top_produtos, chart_categoria,
    chart_scatter_margem_volume,
)

setup_page("Análise de Produtos", "Performance, margem e alertas por produto e categoria", "📦")

df, *_ = load_all()
df = sidebar_filters(df, show_canal=False, show_categoria=True)

# ── KPIs produtos ──────────────────────────────────────────────────────────────
section("Indicadores de Produtos")
df_marg = margem_por_produto(df)
n_negativo = (df_marg["margem_pct"] < 0).sum()

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("Receita Líquida Total", fmt_brl(receita_liquida_total(df))), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Margem Bruta Média", f"{margem_pct(df):.1f}%",
                         color="success" if margem_pct(df) > 0 else "danger"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Produtos Analisados", str(len(df_marg)),
                         sub="no período filtrado", color="neutral"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Produtos c/ Margem Negativa", str(n_negativo),
                         color="danger" if n_negativo > 0 else "success"), unsafe_allow_html=True)

st.space("small")

# ── top produtos + scatter ─────────────────────────────────────────────────────
section("Ranking por Receita")
df_top = top_produtos(df, n=10)
if not df_top.empty:
    st.plotly_chart(chart_top_produtos(df_top, n=10, height=420))

section("Margem × Volume (Scatter)")
if not df_marg.empty:
    st.plotly_chart(chart_scatter_margem_volume(df_marg, height=460))
    insight(
        "Como ler este gráfico",
        "Cada bolha é um produto. O eixo X mostra o volume vendido, "
        "o eixo Y a margem bruta (%) e o tamanho da bolha representa a receita. "
        "Produtos acima de 0% e à direita são os mais saudáveis."
    )

# ── margem por categoria ───────────────────────────────────────────────────────
section("Receita & Margem por Categoria")
df_cat = receita_por_categoria(df)
if not df_cat.empty:
    st.plotly_chart(chart_categoria(df_cat, height=360))

# ── alertas de margem negativa ────────────────────────────────────────────────
negativos = df_marg[df_marg["margem_pct"] < 0].sort_values("margem_pct")
if not negativos.empty:
    section("⚠️ Alertas — Produtos com Margem Negativa")
    st.error(f"{len(negativos)} produto(s) com margem negativa no período selecionado.")
    st.dataframe(
        negativos[["nome_produto", "categoria", "receita", "lucro", "margem_pct"]]
        .rename(columns={
            "nome_produto": "Produto",
            "categoria":    "Categoria",
            "receita":      "Receita (R$)",
            "lucro":        "Lucro (R$)",
            "margem_pct":   "Margem (%)",
        })
        .style.format({"Receita (R$)": "{:,.2f}", "Lucro (R$)": "{:,.2f}", "Margem (%)": "{:.1f}"})
               .background_gradient(subset=["Margem (%)"], cmap="RdYlGn"),
    )
else:
    st.success("Nenhum produto com margem negativa no período selecionado.")

# ── tabela completa ───────────────────────────────────────────────────────────
with st.expander("📋 Ver tabela completa de produtos"):
    st.dataframe(
        df_marg[["nome_produto", "categoria", "qtd", "receita", "lucro", "margem_pct"]]
        .sort_values("receita", ascending=False)
        .rename(columns={
            "nome_produto": "Produto",
            "categoria":    "Categoria",
            "qtd":          "Qtd Vendida",
            "receita":      "Receita (R$)",
            "lucro":        "Lucro (R$)",
            "margem_pct":   "Margem (%)",
        })
        .style.format({"Receita (R$)": "{:,.2f}", "Lucro (R$)": "{:,.2f}", "Margem (%)": "{:.1f}"}),
        height=400,
    )
