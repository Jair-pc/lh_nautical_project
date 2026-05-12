# LH Nautical — Guia de Integração Power BI

## Arquivos Gold para Importação

Todos os arquivos abaixo ficam em `data/gold/` e são gerados automaticamente
ao executar `python main.py`.

| Arquivo                 | Tipo    | Uso no Power BI                            |
|-------------------------|---------|--------------------------------------------|
| `fato_vendas.parquet`   | Fato    | Base de todas as visualizações             |
| `dim_clientes.parquet`  | Dimensão| Segmentação e filtros de cliente           |
| `dim_produtos.parquet`  | Dimensão| Filtros de produto e categoria             |

---

## Como Conectar ao Power BI Desktop

1. **Power BI Desktop** → Get Data → Parquet
2. Navegar até `data/gold/fato_vendas.parquet`
3. Repetir para `dim_clientes.parquet` e `dim_produtos.parquet`
4. No **Model View**, criar relacionamentos:
   - `fato_vendas[id_cliente]` → `dim_clientes[id_cliente]` (Many:1)
   - `fato_vendas[id_produto]` → `dim_produtos[id_produto]` (Many:1)

---

## KPIs Recomendados (Cartões)

```dax
-- Receita Líquida Total
Receita Líquida = 
CALCULATE(
    SUM(fato_vendas[receita_liquida]),
    fato_vendas[status_venda] = "concluida"
)

-- Margem Bruta %
Margem % = 
DIVIDE(
    CALCULATE(SUM(fato_vendas[lucro_bruto]), fato_vendas[status_venda] = "concluida"),
    CALCULATE(SUM(fato_vendas[receita_liquida]), fato_vendas[status_venda] = "concluida")
) * 100

-- Ticket Médio
Ticket Médio = 
AVERAGEX(
    FILTER(fato_vendas, fato_vendas[status_venda] = "concluida"),
    fato_vendas[receita_liquida]
)

-- Total de Pedidos
Total Pedidos = 
CALCULATE(
    DISTINCTCOUNT(fato_vendas[id_venda]),
    fato_vendas[status_venda] = "concluida"
)
```

---

## Visuais Recomendados

### Página 1 — Visão Geral Executiva
- **4 cartões KPI:** Receita, Lucro, Margem, Ticket Médio
- **Gráfico de linha:** Evolução mensal de receita (ano × mês)
- **Gráfico de barras:** Receita por canal de venda
- **Segmentador:** Ano, Mês, Canal

### Página 2 — Produtos
- **Gráfico de barras horizontal:** Top 10 produtos por receita
- **Gráfico de dispersão:** Margem % × Volume de vendas (por produto)
- **Tabela:** Produtos com menor margem (alerta)
- **Segmentador:** Categoria, Subcategoria

### Página 3 — Clientes
- **Gráfico de barras:** Top 10 clientes por receita
- **Mapa:** Distribuição geográfica (por estado)
- **Gráfico de pizza:** Participação por segmento de cliente
- **Segmentador:** Estado, Segmento

### Página 4 — Temporal
- **Gráfico de área:** Faturamento por mês (com destaque em alta temporada)
- **Gráfico de barras:** Vendas por dia da semana
- **Matriz:** Mês × Ano (comparativo YoY)
- **Segmentador:** Ano

---

## Paleta de Cores LH Nautical

```
Azul Principal:  #1565C0
Verde Sucesso:   #2E7D32
Laranja Alerta:  #E65100
Cinza Neutro:    #546E7A
Fundo:           #F5F5F5
```
