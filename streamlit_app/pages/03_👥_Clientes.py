import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.data_loader import load_all
from src.filters import setup_page, sidebar_filters, kpi_card, insight, section
from src.metrics import (
    total_clientes_unicos, receita_por_cliente, pedidos_por_cliente,
    top_clientes, receita_por_estado, segmentacao_clientes,
    receita_liquida_total, fmt_brl,
)
from src.charts import (
    chart_top_clientes, chart_segmentacao, chart_receita_estado,
)

setup_page("Análise de Clientes", "Segmentação, distribuição geográfica e ranking de clientes", "👥")

df, *_ = load_all()
df = sidebar_filters(df, show_canal=True, show_segmento=True, show_estado=True)

# ── KPIs clientes ─────────────────────────────────────────────────────────────
section("Indicadores de Clientes")
k1, k2, k3, k4 = st.columns(4)
df_seg = segmentacao_clientes(df)
with k1:
    st.markdown(kpi_card("Clientes Únicos", f"{total_clientes_unicos(df):,}",
                         color="primary"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Receita por Cliente", fmt_brl(receita_por_cliente(df)),
                         color="success"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Pedidos por Cliente", f"{pedidos_por_cliente(df):.1f}",
                         sub="média", color="neutral"), unsafe_allow_html=True)
with k4:
    top_est = df_seg.iloc[0]["estado"] if not df_seg.empty else "–"
    st.markdown(kpi_card("Estado Líder", top_est, color="neutral"), unsafe_allow_html=True)

st.space("small")

# ── top clientes ───────────────────────────────────────────────────────────────
section("Top 10 Clientes por Receita")
df_top = top_clientes(df, n=10)
if not df_top.empty:
    st.plotly_chart(chart_top_clientes(df_top))

# ── segmentação + estados ──────────────────────────────────────────────────────
section("Segmentação e Geografia")
col_l, col_r = st.columns([1, 1])

with col_l:
    if not df_seg.empty:
        st.plotly_chart(chart_segmentacao(df_seg))

with col_r:
    df_est = receita_por_estado(df)
    if not df_est.empty:
        st.plotly_chart(chart_receita_estado(df_est, height=340))

# ── insight segmento ───────────────────────────────────────────────────────────
if not df_seg.empty:
    est_top = df_seg.iloc[0]
    total   = df_seg["receita"].sum() or 1
    share   = est_top["receita"] / total * 100
    insight(
        "Estado Dominante",
        f"O estado <strong>{est_top['estado']}</strong> concentra "
        f"{share:.1f}% da receita total ({est_top['clientes']} clientes).",
    )

# ── tabela top clientes ───────────────────────────────────────────────────────
with st.expander("📋 Ver tabela completa de clientes"):
    df_full = top_clientes(df, n=999)
    st.dataframe(
        df_full.rename(columns={
            "nome_completo": "Cliente",
            "cidade":        "Cidade",
            "estado":        "Estado",
            "receita":       "Receita (R$)",
            "pedidos":       "Pedidos",
            "qtd":           "Qtd",
        })
        .style.format({"Receita (R$)": "{:,.2f}"}),
        height=400,
    )
