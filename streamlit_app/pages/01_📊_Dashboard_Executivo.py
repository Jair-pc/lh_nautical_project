import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.data_loader import load_all
from src.filters import setup_page, sidebar_filters, kpi_card, insight, section
from src.metrics import (
    receita_liquida_total, receita_bruta_total, lucro_bruto_total,
    margem_pct, ticket_medio, total_pedidos,
    receita_mensal, receita_por_canal, receita_por_categoria,
    top_produtos, top_clientes, stats_cancelamentos, fmt_brl,
)
from src.charts import (
    chart_receita_mensal, chart_canal, chart_categoria,
    chart_top_produtos, chart_top_clientes,
)

setup_page("Dashboard Executivo", "Visão consolidada de receita, margem e performance operacional", "📊")

df, *_ = load_all()
df = sidebar_filters(df, show_canal=True, show_categoria=True)

# ── KPIs ───────────────────────────────────────────────────────────────────────
section("Indicadores-Chave de Performance")
k1, k2, k3, k4, k5 = st.columns(5)

cards = [
    (k1, "Receita Líquida",  fmt_brl(receita_liquida_total(df)), "primary"),
    (k2, "Lucro Bruto",      fmt_brl(lucro_bruto_total(df)),     "success"),
    (k3, "Margem Bruta",     f"{margem_pct(df):.1f}%",           "success" if margem_pct(df) > 20 else "warning"),
    (k4, "Ticket Médio",     fmt_brl(ticket_medio(df)),          "neutral"),
    (k5, "Total de Pedidos", f"{total_pedidos(df):,}",           "neutral"),
]
for col, lbl, val, cls in cards:
    with col:
        st.markdown(kpi_card(lbl, val, color=cls), unsafe_allow_html=True)

st.space("small")

# ── evolução mensal + canal ────────────────────────────────────────────────────
section("Evolução de Receita")
col_l, col_r = st.columns([2, 1])
df_men = receita_mensal(df)

with col_l:
    if df_men.empty:
        st.caption("Sem dados para o período selecionado.")
    else:
        st.plotly_chart(chart_receita_mensal(df_men))

with col_r:
    df_canal = receita_por_canal(df)
    if not df_canal.empty:
        st.plotly_chart(chart_canal(df_canal, height=380))

# ── categoria + top produtos ───────────────────────────────────────────────────
section("Análise por Categoria e Produto")
col_a, col_b = st.columns(2)

with col_a:
    df_cat = receita_por_categoria(df)
    if not df_cat.empty:
        st.plotly_chart(chart_categoria(df_cat))

with col_b:
    df_top_p = top_produtos(df, n=8)
    if not df_top_p.empty:
        st.plotly_chart(chart_top_produtos(df_top_p, n=8, height=340))

# ── top clientes ───────────────────────────────────────────────────────────────
section("Top Clientes")
df_top_c = top_clientes(df, n=10)
if not df_top_c.empty:
    st.plotly_chart(chart_top_clientes(df_top_c))

# ── cancelamentos insight ──────────────────────────────────────────────────────
cancel = stats_cancelamentos(df)
if cancel["n_cancelados"] > 0:
    insight(
        "Atenção — Cancelamentos",
        f"{cancel['n_cancelados']} pedidos cancelados representam "
        f"{cancel['taxa_cancel_pct']:.1f}% do total, com {fmt_brl(cancel['receita_cancelada'])} em receita perdida.",
    )
