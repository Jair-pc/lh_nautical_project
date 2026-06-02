import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.data_loader import load_all
from src.filters import setup_page, sidebar_filters, kpi_card, insight, section
from src.metrics import (
    receita_mensal, vendas_por_dia_semana, heatmap_mes_ano,
    receita_liquida_total, total_pedidos, fmt_brl,
)
from src.charts import (
    chart_receita_mensal, chart_receita_acumulada,
    chart_yoy, chart_dia_semana, chart_heatmap,
)

setup_page("Análise Temporal", "Sazonalidade, crescimento e comparativos anuais de receita", "📈")

df, *_ = load_all()
df = sidebar_filters(df, show_canal=True)

df_men = receita_mensal(df)

# ── KPIs temporais ────────────────────────────────────────────────────────────
section("Indicadores do Período")
k1, k2, k3, k4 = st.columns(4)

melhor_mes = df_men.loc[df_men["receita"].idxmax()] if not df_men.empty else None
pior_mes   = df_men.loc[df_men["receita"].idxmin()]  if not df_men.empty else None

with k1:
    st.markdown(kpi_card("Receita Total no Período", fmt_brl(receita_liquida_total(df)),
                         color="primary"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Total de Pedidos", f"{total_pedidos(df):,}",
                         color="neutral"), unsafe_allow_html=True)
with k3:
    val = fmt_brl(melhor_mes["receita"]) + f" ({melhor_mes['ano_mes']})" if melhor_mes is not None else "–"
    st.markdown(kpi_card("Melhor Mês", val, color="success"), unsafe_allow_html=True)
with k4:
    val = fmt_brl(pior_mes["receita"]) + f" ({pior_mes['ano_mes']})" if pior_mes is not None else "–"
    st.markdown(kpi_card("Mês Mais Fraco", val, color="warning"), unsafe_allow_html=True)

st.space("small")

# ── linha mensal + acumulada ───────────────────────────────────────────────────
section("Tendência de Receita")
col_l, col_r = st.columns(2)
with col_l:
    if not df_men.empty:
        st.plotly_chart(chart_receita_mensal(df_men))
    else:
        st.caption("Sem dados para o período selecionado.")
with col_r:
    if not df_men.empty:
        st.plotly_chart(chart_receita_acumulada(df_men))

# ── YoY ───────────────────────────────────────────────────────────────────────
section("Comparativo Ano a Ano (YoY)")
if not df_men.empty:
    st.plotly_chart(chart_yoy(df_men, height=380))

    anos = sorted(df_men["ano"].unique())
    if len(anos) >= 2:
        rec_atual    = df_men[df_men["ano"] == anos[-1]]["receita"].sum()
        rec_anterior = df_men[df_men["ano"] == anos[-2]]["receita"].sum()
        if rec_anterior:
            delta = (rec_atual - rec_anterior) / rec_anterior * 100
            sinal = "crescimento" if delta > 0 else "retração"
            insight(
                f"YoY {anos[-2]} → {anos[-1]}",
                f"A receita apresentou <strong>{sinal} de {abs(delta):.1f}%</strong> "
                f"em relação ao ano anterior ({fmt_brl(rec_anterior)} → {fmt_brl(rec_atual)}).",
            )

# ── dia da semana + heatmap ────────────────────────────────────────────────────
section("Padrões de Sazonalidade")
col_a, col_b = st.columns(2)

with col_a:
    df_dia = vendas_por_dia_semana(df)
    if not df_dia.empty:
        st.plotly_chart(chart_dia_semana(df_dia))

with col_b:
    pivot = heatmap_mes_ano(df)
    if not pivot.empty:
        st.plotly_chart(chart_heatmap(pivot))
