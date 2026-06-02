import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from src.data_loader import load_all
from src.metrics import (
    receita_liquida_total, lucro_bruto_total, margem_pct,
    ticket_medio, total_pedidos, total_clientes_unicos, stats_cancelamentos,
    fmt_brl,
)
from src.filters import _load_css

st.set_page_config(
    page_title="LH Nautical Analytics",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)
_load_css()

# ── sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    """<div class="sidebar-logo">
        <div class="company-name">⚓ LH Nautical</div>
        <div class="company-sub">Analytics Platform</div>
    </div>""",
    unsafe_allow_html=True,
)
st.sidebar.caption("Use o menu acima para navegar entre as páginas.")

# ── header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """<div class="main-header">
        <h1>⚓ LH Nautical — Analytics Platform</h1>
        <p>Plataforma corporativa de Business Intelligence · Dados Gold · Florianópolis, SC</p>
    </div>""",
    unsafe_allow_html=True,
)

# ── carrega dados ──────────────────────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    df, fato, clientes, produtos = load_all()

df_ok = df[df["status_venda"] == "concluida"]

# ── métricas rápidas ───────────────────────────────────────────────────────────
st.markdown("### Visão Rápida — Dados Consolidados")

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric("Receita Líquida", fmt_brl(receita_liquida_total(df)))
with c2:
    st.metric("Lucro Bruto", fmt_brl(lucro_bruto_total(df)))
with c3:
    st.metric("Margem Bruta", f"{margem_pct(df):.1f}%")
with c4:
    st.metric("Ticket Médio", fmt_brl(ticket_medio(df)))
with c5:
    st.metric("Total Pedidos", f"{total_pedidos(df):,}")
with c6:
    st.metric("Clientes Únicos", f"{total_clientes_unicos(df):,}")

st.space("small")

# ── visão do pipeline ─────────────────────────────────────────────────────────
st.markdown("### Arquitetura do Projeto")
col_l, col_r = st.columns([2, 1])

with col_l:
    st.markdown("""
    | Camada | Registros | Descrição |
    |--------|-----------|-----------|
    | 🟤 **RAW**    | Dados brutos | Arquivos CSV originais com inconsistências |
    | 🟠 **BRONZE** | Ingestão     | Dados carregados sem transformação |
    | ⚪ **SILVER** | Limpeza      | Normalização, deduplicação, validação |
    | 🟡 **GOLD**   | Analítico    | Fato + Dimensões prontos para BI |
    """)

with col_r:
    cancel = stats_cancelamentos(df)
    st.markdown("""
    <div class="kpi-card warning" style="margin-bottom:0.7rem">
        <div class="kpi-label">Taxa de Cancelamento</div>
        <div class="kpi-value">{:.1f}%</div>
        <div class="kpi-sub">{} pedidos cancelados</div>
    </div>
    <div class="kpi-card neutral">
        <div class="kpi-label">Produtos no Catálogo</div>
        <div class="kpi-value">{:,}</div>
        <div class="kpi-sub">{} categorias</div>
    </div>
    """.format(
        cancel["taxa_cancel_pct"],
        cancel["n_cancelados"],
        produtos["id_produto"].nunique(),
        produtos["categoria"].nunique() if "categoria" in produtos.columns else "–",
    ), unsafe_allow_html=True)

st.space("small")

# ── status dos arquivos Gold ──────────────────────────────────────────────────
st.markdown("### Status dos Arquivos Gold")
g1, g2, g3 = st.columns(3)
with g1:
    st.success(f"fato_vendas.parquet — {len(fato):,} linhas")
with g2:
    st.success(f"dim_clientes.parquet — {len(clientes):,} clientes")
with g3:
    st.success(f"dim_produtos.parquet — {len(produtos):,} produtos")

st.space("small")
st.caption("LH Nautical Analytics Platform · Desenvolvido com Streamlit + Plotly · Dados fictícios para portfólio")
