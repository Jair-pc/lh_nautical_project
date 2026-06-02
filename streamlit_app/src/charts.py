import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ── paleta oficial LH Nautical ─────────────────────────────────────────────────
C = {
    "primary":  "#1565C0",
    "success":  "#2E7D32",
    "warning":  "#E65100",
    "neutral":  "#546E7A",
    "danger":   "#C62828",
    "bg":       "#F5F5F5",
    "white":    "#FFFFFF",
}
PALETTE = [
    "#1565C0", "#2E7D32", "#E65100", "#546E7A", "#7B1FA2",
    "#00695C", "#C62828", "#F57F17", "#1B5E20", "#880E4F",
]
TEMPLATE = "plotly_white"


def _color_map(series: pd.Series) -> dict:
    """Map unique values to PALETTE colors — avoids px color_discrete_sequence groupby bug in Plotly 5.24."""
    vals = series.dropna().unique()
    return {v: PALETTE[i % len(PALETTE)] for i, v in enumerate(vals)}


def _base(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#1A237E"), x=0, pad=dict(l=4)),
        template=TEMPLATE,
        height=height,
        margin=dict(l=12, r=12, t=44, b=12),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=12, color="#424242"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#E3F2FD"),
    )
    return fig


# ── financeiro ────────────────────────────────────────────────────────────────

def chart_receita_mensal(df: pd.DataFrame, height: int = 380) -> go.Figure:
    fig = go.Figure()
    for ano, grp in df.groupby("ano"):
        fig.add_trace(go.Scatter(
            x=grp["ano_mes"], y=grp["receita"],
            mode="lines+markers",
            name=str(ano),
            line=dict(width=2.5),
            marker=dict(size=7),
            hovertemplate="%{x}<br>Receita: R$ %{y:,.2f}<extra></extra>",
        ))
    _base(fig, "Evolução Mensal de Receita", height)
    fig.update_xaxes(tickangle=-30, title_text="")
    fig.update_yaxes(title_text="R$", tickformat=",.0f")
    return fig


def chart_receita_acumulada(df: pd.DataFrame, height: int = 380) -> go.Figure:
    df = df.copy().sort_values("ano_mes")
    df["acumulado"] = df["receita"].cumsum()
    fig = go.Figure(go.Scatter(
        x=df["ano_mes"], y=df["acumulado"],
        mode="lines",
        fill="tozeroy",
        line=dict(color=C["primary"], width=2.5),
        fillcolor="rgba(21,101,192,0.12)",
        hovertemplate="%{x}<br>Acumulado: R$ %{y:,.2f}<extra></extra>",
    ))
    _base(fig, "Receita Acumulada", height)
    fig.update_xaxes(tickangle=-30, title_text="")
    fig.update_yaxes(title_text="R$", tickformat=",.0f")
    return fig


def chart_canal(df: pd.DataFrame, height: int = 340) -> go.Figure:
    fig = px.bar(df, x="canal_venda", y="receita",
                 color="canal_venda", color_discrete_map=_color_map(df["canal_venda"]),
                 text="receita",
                 custom_data=["share_pct"])
    fig.update_traces(
        texttemplate="R$ %{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.2f}<br>Share: %{customdata[0]:.1f}%<extra></extra>",
    )
    _base(fig, "Receita por Canal de Venda", height)
    fig.update_yaxes(title_text="R$", tickformat=",.0f")
    fig.update_xaxes(title_text="")
    fig.update_layout(showlegend=False)
    return fig


def chart_categoria(df: pd.DataFrame, height: int = 340) -> go.Figure:
    df = df.sort_values("receita")
    fig = px.bar(df, y="categoria", x="receita",
                 orientation="h", color="margem_pct",
                 color_continuous_scale=[[0, C["danger"]], [0.5, C["warning"]], [1, C["success"]]],
                 text="receita",
                 hover_data={"margem_pct": ":.1f"})
    fig.update_traces(
        texttemplate="R$ %{text:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.2f}<br>Margem: %{customdata[0]:.1f}%<extra></extra>",
    )
    _base(fig, "Receita & Margem por Categoria", height)
    fig.update_xaxes(title_text="R$", tickformat=",.0f")
    fig.update_yaxes(title_text="")
    fig.update_coloraxes(colorbar_title="Margem %")
    return fig


# ── produtos ──────────────────────────────────────────────────────────────────

def chart_top_produtos(df: pd.DataFrame, n: int = 10, height: int = 400) -> go.Figure:
    df = df.head(n).sort_values("receita")
    fig = px.bar(df, y="nome_produto", x="receita", orientation="h",
                 color="categoria", color_discrete_map=_color_map(df["categoria"]),
                 text="receita",
                 hover_data={"margem_pct": ":.1f", "qtd": True})
    fig.update_traces(
        texttemplate="R$ %{text:,.0f}", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.2f}<br>Margem: %{customdata[0]:.1f}%<br>Qtd: %{customdata[1]}<extra></extra>",
    )
    _base(fig, f"Top {n} Produtos por Receita", height)
    fig.update_xaxes(title_text="R$", tickformat=",.0f")
    fig.update_yaxes(title_text="", tickfont=dict(size=11))
    return fig


def chart_scatter_margem_volume(df: pd.DataFrame, height: int = 420) -> go.Figure:
    fig = px.scatter(df, x="qtd", y="margem_pct",
                     size="receita", color="categoria",
                     color_discrete_map=_color_map(df["categoria"]),
                     hover_name="nome_produto",
                     hover_data={"receita": ":,.2f", "qtd": True, "margem_pct": ":.1f"},
                     size_max=45)
    fig.add_hline(y=0, line_dash="dash", line_color=C["danger"], opacity=0.6,
                  annotation_text="Margem zero", annotation_position="right")
    _base(fig, "Margem % × Volume Vendido (bolha = Receita)", height)
    fig.update_xaxes(title_text="Quantidade Vendida")
    fig.update_yaxes(title_text="Margem Bruta (%)")
    return fig


# ── clientes ──────────────────────────────────────────────────────────────────

def chart_top_clientes(df: pd.DataFrame, n: int = 10, height: int = 400) -> go.Figure:
    df = df.head(n).sort_values("receita")
    fig = px.bar(df, y="nome_completo", x="receita", orientation="h",
                 color="estado", color_discrete_map=_color_map(df["estado"]),
                 text="receita",
                 hover_data={"pedidos": True, "estado": True})
    fig.update_traces(
        texttemplate="R$ %{text:,.0f}", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.2f}<br>Pedidos: %{customdata[0]}<br>Estado: %{customdata[1]}<extra></extra>",
    )
    _base(fig, f"Top {n} Clientes por Receita", height)
    fig.update_xaxes(title_text="R$", tickformat=",.0f")
    fig.update_yaxes(title_text="", tickfont=dict(size=11))
    return fig


def chart_segmentacao(df: pd.DataFrame, height: int = 340) -> go.Figure:
    # df tem coluna "estado" (segmento ausente nos dados reais)
    col = "estado" if "estado" in df.columns else df.columns[0]
    fig = px.pie(df, names=col, values="receita",
                 color_discrete_sequence=PALETTE,
                 hole=0.42)
    fig.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Receita: R$ %{value:,.2f}<br>Share: %{percent}<extra></extra>",
    )
    _base(fig, "Receita por Estado (Top 8)", height)
    return fig


def chart_receita_estado(df: pd.DataFrame, height: int = 380) -> go.Figure:
    df = df.sort_values("receita")
    fig = px.bar(df, y="estado", x="receita", orientation="h",
                 color="receita",
                 color_continuous_scale=[[0, "#BBDEFB"], [1, C["primary"]]],
                 text="receita")
    fig.update_traces(
        texttemplate="R$ %{text:,.0f}", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.2f}<extra></extra>",
    )
    _base(fig, "Receita por Estado (UF)", height)
    fig.update_xaxes(title_text="R$", tickformat=",.0f")
    fig.update_yaxes(title_text="")
    fig.update_coloraxes(showscale=False)
    return fig


# ── temporal ──────────────────────────────────────────────────────────────────

def chart_yoy(df: pd.DataFrame, height: int = 380) -> go.Figure:
    fig = go.Figure()
    anos = sorted(df["ano"].unique())
    cores = PALETTE[:len(anos)]
    for i, ano in enumerate(anos):
        grp = df[df["ano"] == ano]
        fig.add_trace(go.Bar(
            name=str(ano),
            x=grp["mes_nome"], y=grp["receita"],
            marker_color=cores[i],
            hovertemplate=f"{ano} — %{{x}}<br>Receita: R$ %{{y:,.2f}}<extra></extra>",
        ))
    _base(fig, "Comparativo Anual de Receita (YoY)", height)
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Mês")
    fig.update_yaxes(title_text="R$", tickformat=",.0f")
    return fig


def chart_dia_semana(df: pd.DataFrame, height: int = 340) -> go.Figure:
    colors = [C["primary"] if p > df["pedidos"].median() else "#90CAF9"
              for p in df["pedidos"]]
    fig = go.Figure(go.Bar(
        x=df["dia_semana"], y=df["receita"],
        marker_color=colors,
        text=df["pedidos"],
        texttemplate="%{text} ped.",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.2f}<br>Pedidos: %{text}<extra></extra>",
    ))
    _base(fig, "Receita por Dia da Semana", height)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="R$", tickformat=",.0f")
    return fig


def chart_heatmap(pivot: pd.DataFrame, height: int = 340) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.astype(str).tolist(),
        y=[f"Mês {m}" for m in pivot.index.tolist()],
        colorscale=[[0, "#E3F2FD"], [0.5, C["primary"]], [1, "#0D47A1"]],
        hoverongaps=False,
        hovertemplate="Ano: %{x}<br>%{y}<br>Receita: R$ %{z:,.2f}<extra></extra>",
        text=[[f"R$ {v:,.0f}" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10, color="white"),
    ))
    _base(fig, "Heatmap de Receita — Mês × Ano", height)
    fig.update_xaxes(title_text="Ano")
    fig.update_yaxes(title_text="Mês")
    return fig


# ── forecast ─────────────────────────────────────────────────────────────────

def chart_forecast(hist: pd.DataFrame, forecast: pd.DataFrame,
                   ma: pd.DataFrame, height: int = 440) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist["ano_mes"], y=hist["receita"],
        mode="lines+markers", name="Histórico",
        line=dict(color=C["primary"], width=2.5),
        marker=dict(size=6),
        hovertemplate="%{x}<br>Receita: R$ %{y:,.2f}<extra></extra>",
    ))

    if not ma.empty:
        fig.add_trace(go.Scatter(
            x=ma["ano_mes"], y=ma["ma"],
            mode="lines", name="Média Móvel (3M)",
            line=dict(color=C["neutral"], width=1.8, dash="dot"),
            hovertemplate="%{x}<br>MM: R$ %{y:,.2f}<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=forecast["ano_mes"], y=forecast["upper"],
        mode="lines", line=dict(width=0), showlegend=False,
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=forecast["ano_mes"], y=forecast["lower"],
        mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(46,125,50,0.12)",
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=forecast["ano_mes"], y=forecast["previsao"],
        mode="lines+markers", name="Previsão",
        line=dict(color=C["success"], width=2.5, dash="dash"),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="%{x}<br>Previsão: R$ %{y:,.2f}<extra></extra>",
    ))

    last_x = hist["ano_mes"].iloc[-1]
    fig.add_shape(
        type="line", x0=last_x, x1=last_x, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(dash="dash", color=C["neutral"], width=1.5),
        opacity=0.55,
    )
    fig.add_annotation(
        x=last_x, y=0.98, yref="paper",
        text="Hoje", showarrow=False,
        font=dict(color=C["neutral"], size=11),
        yanchor="top",
    )

    _base(fig, "Previsão de Receita — Média Móvel + Regressão Linear", height)
    fig.update_xaxes(tickangle=-30, title_text="")
    fig.update_yaxes(title_text="R$", tickformat=",.0f")
    return fig


# ── recomendações ─────────────────────────────────────────────────────────────

def chart_popularidade(df: pd.DataFrame, height: int = 380) -> go.Figure:
    df = df.sort_values("qtd")
    fig = px.bar(df, y="nome_produto", x="qtd", orientation="h",
                 color="categoria", color_discrete_map=_color_map(df["categoria"]),
                 text="qtd",
                 hover_data={"receita": ":,.2f"})
    fig.update_traces(
        texttemplate="%{text} un.", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Qtd: %{x}<br>Receita: R$ %{customdata[0]:,.2f}<extra></extra>",
    )
    _base(fig, "Produtos Mais Vendidos (Popularidade)", height)
    fig.update_xaxes(title_text="Quantidade Vendida")
    fig.update_yaxes(title_text="", tickfont=dict(size=11))
    return fig
