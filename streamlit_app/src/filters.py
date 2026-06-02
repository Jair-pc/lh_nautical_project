import streamlit as st
import pandas as pd
from pathlib import Path


def _load_css() -> None:
    css_path = Path(__file__).parent.parent / "assets" / "styles.css"
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def setup_page(title: str, subtitle: str, icon: str = "⚓") -> None:
    st.set_page_config(
        page_title=f"{title} | LH Nautical",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _load_css()
    st.markdown(
        f"""<div class="main-header">
            <h1>{icon} {title}</h1>
            <p>{subtitle}</p>
        </div>""",
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """<div class="sidebar-logo">
            <div class="company-name">⚓ LH Nautical</div>
            <div class="company-sub">Analytics Platform</div>
        </div>""",
        unsafe_allow_html=True,
    )


def sidebar_filters(
    df: pd.DataFrame,
    show_canal: bool = True,
    show_categoria: bool = False,
    show_segmento: bool = False,
    show_estado: bool = False,
) -> pd.DataFrame:
    sidebar_brand()
    st.sidebar.markdown("### Filtros")

    anos = sorted(df["ano"].dropna().unique().tolist())
    sel_anos = st.sidebar.multiselect("Ano", anos, default=anos, key="f_ano")

    meses_disp = sorted(df[df["ano"].isin(sel_anos)]["mes"].dropna().unique().tolist())
    sel_meses  = st.sidebar.multiselect("Mês", meses_disp, default=meses_disp, key="f_mes")

    mask = df["ano"].isin(sel_anos) & df["mes"].isin(sel_meses)

    if show_canal and "canal_venda" in df.columns:
        canais    = sorted(df[mask]["canal_venda"].dropna().unique().tolist())
        sel_canal = st.sidebar.multiselect("Canal de Venda", canais, default=canais, key="f_canal")
        mask &= df["canal_venda"].isin(sel_canal)

    if show_categoria and "categoria" in df.columns:
        cats     = sorted(df[mask]["categoria"].dropna().unique().tolist())
        sel_cat  = st.sidebar.multiselect("Categoria", cats, default=cats, key="f_cat")
        mask &= df["categoria"].isin(sel_cat)

    if show_segmento and "segmento" in df.columns:
        segs     = sorted(df[mask]["segmento"].dropna().unique().tolist())
        sel_seg  = st.sidebar.multiselect("Segmento", segs, default=segs, key="f_seg")
        mask &= df["segmento"].isin(sel_seg)

    if show_estado and "estado" in df.columns:
        estados  = sorted(df[mask]["estado"].dropna().unique().tolist())
        sel_est  = st.sidebar.multiselect("Estado (UF)", estados, default=estados, key="f_est")
        mask &= df["estado"].isin(sel_est)

    n = mask.sum()
    st.sidebar.caption(f"📦 {n:,} registros filtrados")
    return df[mask].copy()


def kpi_card(label: str, value: str, sub: str = "", color: str = "") -> str:
    cls = f"kpi-card {color}".strip()
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="{cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
    </div>"""


def insight(title: str, text: str) -> None:
    st.markdown(
        f"""<div class="insight-box">
            <div class="ititle">💡 {title}</div>
            <div class="itext">{text}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
