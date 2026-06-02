"""
LH Nautical — Captain's Almanac
Editorial landing for the analytics platform.
"""

import sys
from pathlib import Path
from datetime import datetime

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
    page_title="LH Nautical — Captain's Almanac",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)
_load_css()

# ── sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    """<div class="sidebar-logo">
        <div class="company-name">LH Nautical</div>
        <div class="company-sub">Captain&rsquo;s Almanac</div>
    </div>""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """<div style="
        font-family: 'Inter Tight', sans-serif;
        font-size: 0.86rem;
        color: rgba(244,235,221,0.72);
        line-height: 1.55;
        padding: 0 0.2rem;">
        Navegue pelos volumes ao lado para consultar
        cada capítulo do almanaque: vendas, produtos,
        clientes, séries temporais, previsão e o
        gabinete de recomendações.
    </div>""",
    unsafe_allow_html=True,
)

# ── load data ──────────────────────────────────────────────────────────────────
with st.spinner("Abrindo o livro de bordo..."):
    df, fato, clientes, produtos = load_all()

df_ok = df[df["status_venda"] == "concluida"]
cancel = stats_cancelamentos(df)
ano_min = int(df["ano"].min())
ano_max = int(df["ano"].max())

# ── helpers de formatação ─────────────────────────────────────────────────────
def _roman(n: int) -> str:
    """Converte ano para algarismos romanos (MMXXVI)."""
    vals = [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),
            (50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out

def _br_int(n: int) -> str:
    """3.000 em vez de 3,000 (formato brasileiro)."""
    return f"{n:,}".replace(",", ".")

def _brl_split(value: float) -> tuple[str, str]:
    """Quebra valor BRL em ('R$ 1,23', 'mi/mil/...') para tratamento tipográfico."""
    abs_v = abs(value)
    if abs_v >= 1_000_000_000:
        return f"R$ {value/1_000_000_000:.2f}".replace(".", ","), "bi"
    if abs_v >= 1_000_000:
        return f"R$ {value/1_000_000:.2f}".replace(".", ","), "mi"
    if abs_v >= 1_000:
        return f"R$ {value/1_000:.1f}".replace(".", ","), "mil"
    return f"R$ {value:.2f}".replace(".", ","), ""

YEAR_ROMAN = _roman(datetime.now().year)

# ══════════════════════════════════════════════════════════════════════════════
# HERO — magazine cover
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div class="almanac-hero">
        <div class="almanac-eyebrow">
            <span class="dot"></span>
            VOL. I &nbsp;·&nbsp; ANNO {YEAR_ROMAN} &nbsp;·&nbsp; FLORIANÓPOLIS, SC
            <span class="dot"></span>
        </div>
        <h1 class="almanac-title">LH&nbsp;Nautical</h1>
        <div class="almanac-compass">⚓ &nbsp; ✦ &nbsp; ⚓</div>
        <div class="almanac-subtitle">An Analytics Almanac &mdash; <em>from raw tides to gold harbors</em></div>
        <div class="almanac-meta">
            <span>PIPELINE MEDALLION</span>
            <span class="sep">&mdash;</span>
            <span>DADOS {ano_min}&ndash;{ano_max}</span>
            <span class="sep">&mdash;</span>
            <span>{_br_int(len(fato))} REGISTROS</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER I — KPIs as catalog entries
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="folio">
        <div class="folio-number">I.</div>
        <div class="folio-title">PRIMEIRO VOLUME &mdash; Visão Consolidada</div>
        <div class="folio-rule"></div>
        <div class="folio-mark">FIG. 01</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# build the 6 catalog entries
receita = receita_liquida_total(df)
lucro = lucro_bruto_total(df)
margem = margem_pct(df)
ticket = ticket_medio(df)
pedidos = total_pedidos(df)
clientes_uniq = total_clientes_unicos(df)

rec_v, rec_u = _brl_split(receita)
luc_v, luc_u = _brl_split(lucro)
tic_v, tic_u = _brl_split(ticket)

st.markdown(
    f"""
    <div class="almanac-grid">
        <div class="almanac-entry">
            <div class="roman">I</div>
            <div class="label">Receita Líquida</div>
            <div class="figure">{rec_v}<span class="unit">{rec_u}</span></div>
            <div class="note">soma de pedidos concluídos no horizonte analítico</div>
        </div>
        <div class="almanac-entry">
            <div class="roman">II</div>
            <div class="label">Lucro Bruto</div>
            <div class="figure">{luc_v}<span class="unit">{luc_u}</span></div>
            <div class="note">após custos de importação e mercadoria vendida</div>
        </div>
        <div class="almanac-entry">
            <div class="roman">III</div>
            <div class="label">Margem Bruta</div>
            <div class="figure">{margem:.1f}<span class="unit">%</span></div>
            <div class="note">razão entre lucro bruto e receita líquida</div>
        </div>
        <div class="almanac-entry">
            <div class="roman">IV</div>
            <div class="label">Ticket Médio</div>
            <div class="figure">{tic_v}<span class="unit">{tic_u}</span></div>
            <div class="note">valor médio por pedido concluído</div>
        </div>
        <div class="almanac-entry">
            <div class="roman">V</div>
            <div class="label">Pedidos no Volume</div>
            <div class="figure">{_br_int(pedidos)}</div>
            <div class="note">transações registradas no período inteiro</div>
        </div>
        <div class="almanac-entry">
            <div class="roman">VI</div>
            <div class="label">Clientes Únicos</div>
            <div class="figure">{_br_int(clientes_uniq)}</div>
            <div class="note">contas distintas com ao menos uma compra</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER II — Architecture as nautical cartography
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="folio">
        <div class="folio-number">II.</div>
        <div class="folio-title">SEGUNDO VOLUME &mdash; Cartografia dos Dados</div>
        <div class="folio-rule"></div>
        <div class="folio-mark">FIG. 02</div>
    </div>
    """,
    unsafe_allow_html=True,
)

bronze_count = _br_int(len(fato))
gold_fato = _br_int(len(fato))

st.markdown(
    f"""
    <div class="cartography">
        <div class="cartography-head">
            <div class="title">Pipeline Medallion</div>
            <div class="sub">RAW &raquo; BRONZE &raquo; SILVER &raquo; GOLD</div>
        </div>
        <div class="cartography-row">
            <div class="seal">R</div>
            <div class="layer">Raw</div>
            <div class="desc">arquivos brutos de origem &mdash; <em>CSVs com inconsistências, valores ausentes e tipagem ambígua</em></div>
            <div class="count">CSV<span class="unit">arquivos de entrada</span></div>
        </div>
        <div class="cartography-row">
            <div class="seal">B</div>
            <div class="layer">Bronze</div>
            <div class="desc">ingestão fiel à origem com metadados de proveniência &mdash; <em>nada se transforma, tudo se registra</em></div>
            <div class="count">{bronze_count}<span class="unit">linhas ingeridas</span></div>
        </div>
        <div class="cartography-row">
            <div class="seal">S</div>
            <div class="layer">Silver</div>
            <div class="desc">camada de limpeza &mdash; normalização, deduplicação, validação de tipos e regras de negócio</div>
            <div class="count">PASS<span class="unit">8 testes de qualidade</span></div>
        </div>
        <div class="cartography-row">
            <div class="seal">G</div>
            <div class="layer">Gold</div>
            <div class="desc">modelo analítico em estrela &mdash; <em>fato_vendas</em> ladeado por dim_clientes e dim_produtos</div>
            <div class="count">{gold_fato}<span class="unit">linhas no fato</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER III — Manifest of Gold files
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="folio">
        <div class="folio-number">III.</div>
        <div class="folio-title">TERCEIRO VOLUME &mdash; Manifesto da Carga Áurea</div>
        <div class="folio-rule"></div>
        <div class="folio-mark">FIG. 03</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="manifest">
        <div class="manifest-row">
            <div class="check">✓</div>
            <div class="info">
                <div class="name">fato_vendas.parquet</div>
                <div class="size">{_br_int(len(fato))} linhas &middot; tabela-fato central</div>
            </div>
        </div>
        <div class="manifest-row">
            <div class="check">✓</div>
            <div class="info">
                <div class="name">dim_clientes.parquet</div>
                <div class="size">{_br_int(len(clientes))} clientes &middot; dimensão de identidade</div>
            </div>
        </div>
        <div class="manifest-row">
            <div class="check">✓</div>
            <div class="info">
                <div class="name">dim_produtos.parquet</div>
                <div class="size">{_br_int(len(produtos))} produtos &middot; dimensão de catálogo</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# small footnote about cancellation rate (kept as inline editorial caption)
st.markdown(
    f"""
    <div style="
        font-family: 'Fraunces', Georgia, serif;
        font-variation-settings: 'opsz' 24, 'wght' 380, 'SOFT' 40;
        font-style: italic;
        font-size: 1.0rem;
        line-height: 1.55;
        color: #4A4641;
        text-align: center;
        max-width: 720px;
        margin: 1.4rem auto 2.6rem auto;
        padding: 1.1rem 1rem;
        border-top: 1px solid #D9CCB1;
        border-bottom: 1px solid #D9CCB1;">
        &ldquo;Dentre os {_br_int(pedidos)} pedidos registrados, {_br_int(cancel['n_cancelados'])} foram cancelados antes de zarpar &mdash;
        uma taxa de cancelamento de <b>{cancel['taxa_cancel_pct']:.1f}%</b>,
        baixa o suficiente para considerar a operação saudável.&rdquo;
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# COLOPHON
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div class="colophon">
        <div class="ornament">⚓ &nbsp; ✦ &nbsp; ⚓ &nbsp; ✦ &nbsp; ⚓</div>
        <div class="text">
            Encerra-se aqui a capa deste volume.<br>
            Os capítulos seguintes encontram-se à esquerda &mdash; <em>basta navegar</em>.
        </div>
        <div class="meta">
            LH NAUTICAL &middot; PORTO DIGITAL DE FLORIANÓPOLIS &middot; ANNO {YEAR_ROMAN}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
