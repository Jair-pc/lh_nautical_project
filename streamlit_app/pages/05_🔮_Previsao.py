import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.data_loader import load_all
from src.filters import setup_page, sidebar_brand, kpi_card, insight, section
from src.metrics import receita_mensal, fmt_brl
from src.forecasting import moving_average, linear_forecast, forecast_report
from src.charts import chart_forecast

setup_page("Previsão de Demanda", "Tendência de receita com Média Móvel e Regressão Linear", "🔮")

df, *_ = load_all()
sidebar_brand()

# ── parâmetros do forecast ────────────────────────────────────────────────────
st.sidebar.markdown("### Parâmetros")
n_ahead = st.sidebar.slider("Meses a prever", min_value=3, max_value=12, value=6)
window  = st.sidebar.slider("Janela média móvel (meses)", min_value=2, max_value=6, value=3)

# ── dados mensais ─────────────────────────────────────────────────────────────
df_men = receita_mensal(df)

if df_men.empty or len(df_men) < 4:
    st.warning("Dados insuficientes para gerar previsão. São necessários ao menos 4 meses de histórico.")
    st.stop()

# ── cálculos ──────────────────────────────────────────────────────────────────
ma       = moving_average(df_men, window=window)
forecast = linear_forecast(df_men, n_ahead=n_ahead)
report   = forecast_report(df_men, n_ahead=n_ahead)

# ── KPIs forecast ─────────────────────────────────────────────────────────────
section("Diagnóstico do Modelo")
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("Meses de Histórico", str(report["n_obs"]),
                         sub="observações usadas", color="neutral"), unsafe_allow_html=True)
with k2:
    r2_pct = report["r2"] * 100
    st.markdown(kpi_card("R² do Modelo", f"{r2_pct:.1f}%",
                         sub="qualidade do ajuste",
                         color="success" if r2_pct > 60 else "warning"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Tendência", report["tendencia"].capitalize(),
                         sub=f"R$ {report['slope']:+,.0f}/mês".replace(",", "."),
                         color="success" if report["slope"] > 0 else "danger"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Média Móvel 3M", fmt_brl(report["media_3m"]),
                         sub="últimos 3 meses", color="primary"), unsafe_allow_html=True)

st.space("small")

# ── gráfico principal ─────────────────────────────────────────────────────────
section("Projeção de Receita")
st.plotly_chart(chart_forecast(df_men, forecast, ma, height=480))

# ── tabela de previsão ────────────────────────────────────────────────────────
section("Valores Previstos")
col_l, col_r = st.columns([1, 1])

with col_l:
    st.dataframe(
        forecast.rename(columns={
            "ano_mes":  "Período",
            "previsao": "Previsão (R$)",
            "lower":    "Limite Inferior (R$)",
            "upper":    "Limite Superior (R$)",
        })
        .style.format({
            "Previsão (R$)":         "{:,.2f}",
            "Limite Inferior (R$)":  "{:,.2f}",
            "Limite Superior (R$)":  "{:,.2f}",
        }),
    )

with col_r:
    insight(
        "Metodologia",
        "A previsão combina <strong>Média Móvel</strong> (suavização da série histórica) "
        "com <strong>Regressão Linear</strong> (tendência de longo prazo). "
        "A faixa sombreada representa ±1,5 desvio-padrão dos resíduos do modelo."
    )
    if report["r2"] < 0.4:
        st.warning(
            "⚠️ O R² do modelo está abaixo de 40%, indicando baixa aderência à série histórica. "
            "Use a previsão como referência qualitativa apenas."
        )
    else:
        st.success(
            f"✅ O modelo explica {report['r2']*100:.1f}% da variação histórica da receita. "
            "A previsão tem boa confiabilidade para o curto prazo."
        )

# ── explicação técnica ─────────────────────────────────────────────────────────
with st.expander("📘 Detalhes técnicos do modelo"):
    st.markdown(f"""
**Regressão Linear Simples**
- Variável dependente: Receita mensal (R$)
- Variável independente: índice temporal (t = 0, 1, 2, …)
- Coeficiente angular (slope): **R$ {report['slope']:+,.2f}/mês**
- Intercepto estimado via OLS (Scikit-learn `LinearRegression`)
- Intervalo de confiança: ±1,5σ dos resíduos do treino

**Média Móvel**
- Janela selecionada: **{window} meses**
- Parâmetro `min_periods=1` para não perder os primeiros períodos

**Dados utilizados**
- {report['n_obs']} observações mensais
- Série: `receita_liquida` de pedidos com status `concluida`
""")
