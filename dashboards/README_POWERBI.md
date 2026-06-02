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

## Prompt de Medidas DAX — LH Nautical

> Use este prompt com uma IA (Claude, Copilot, ChatGPT) para gerar ou revisar as medidas DAX do relatório.  
> Copie o bloco abaixo integralmente e cole no chat da IA.

---

```
Contexto do modelo de dados Power BI — LH Nautical:

Tabela FATO: fato_vendas
  - id_venda          : texto (chave única)
  - id_cliente        : inteiro (FK → dim_clientes)
  - id_produto        : inteiro (FK → dim_produtos)
  - data_venda        : data
  - quantidade        : inteiro
  - preco_unitario    : decimal
  - desconto_pct      : decimal (0 a 1; nulo tratado como 0)
  - receita_bruta     : decimal
  - receita_liquida   : decimal (= receita_bruta × (1 − desconto_pct))
  - custo_unitario    : decimal
  - custo_total       : decimal
  - lucro_bruto       : decimal (= receita_liquida − custo_total)
  - canal_venda       : texto  ("Loja Física" | "E-commerce" | "Representante")
  - status_venda      : texto  ("concluida" | "cancelada" | "devolvida")

Tabela DIMENSÃO: dim_clientes
  - id_cliente        : inteiro (PK)
  - nome_cliente      : texto
  - segmento          : texto  ("Pessoa Física" | "Pessoa Jurídica" | "Marina")
  - estado            : texto  (sigla UF, ex.: "SC", "SP")
  - cidade            : texto

Tabela DIMENSÃO: dim_produtos
  - id_produto        : inteiro (PK)
  - nome_produto      : texto
  - categoria         : texto  ("Motor" | "Acessório" | "Vestuário" | "Eletrônico")
  - subcategoria      : texto
  - marca             : texto
  - pais_origem       : texto

Relacionamentos (Many:1):
  fato_vendas[id_cliente] → dim_clientes[id_cliente]
  fato_vendas[id_produto] → dim_produtos[id_produto]

---
Crie as medidas DAX abaixo organizadas por grupo, usando nomes em português,
apenas para vendas com status_venda = "concluida" salvo indicação contrária.

GRUPO 1 — KPIs Financeiros Principais
  1.  Receita Bruta Total    : soma de receita_bruta (vendas concluídas)
  2.  Receita Líquida Total  : soma de receita_liquida (vendas concluídas)
  3.  Custo Total            : soma de custo_total (vendas concluídas)
  4.  Lucro Bruto            : soma de lucro_bruto (vendas concluídas)
  5.  Margem Bruta %         : Lucro Bruto ÷ Receita Líquida Total × 100
  6.  Ticket Médio           : média de receita_liquida por pedido (concluídas)
  7.  Total Pedidos          : contagem distinta de id_venda (concluídas)
  8.  Quantidade Total       : soma de quantidade (concluídas)

GRUPO 2 — Inteligência Temporal (requer tabela de calendário)
  9.  Receita YTD            : Receita Líquida Total acumulada no ano até a data selecionada (TOTALYTD)
  10. Receita Mês Anterior   : Receita Líquida Total do mês imediatamente anterior (DATEADD −1 mês)
  11. Variação MoM R$        : Receita Líquida Total − Receita Mês Anterior
  12. Variação MoM %         : Variação MoM R$ ÷ Receita Mês Anterior × 100
  13. Receita Ano Anterior   : Receita Líquida Total do mesmo período do ano passado (SAMEPERIODLASTYEAR)
  14. Variação YoY %         : (Receita Líquida Total − Receita Ano Anterior) ÷ Receita Ano Anterior × 100

GRUPO 3 — Análise de Clientes
  15. Total Clientes Únicos  : contagem distinta de id_cliente (todas as vendas concluídas)
  16. Receita por Cliente    : Receita Líquida Total ÷ Total Clientes Únicos
  17. Pedidos por Cliente    : Total Pedidos ÷ Total Clientes Únicos
  18. Top Cliente Receita    : nome do cliente com maior Receita Líquida (TOPN + MAXX)

GRUPO 4 — Análise de Produtos e Canais
  19. Receita por Categoria  : Receita Líquida Total filtrado pela categoria selecionada
  20. Margem por Categoria % : Lucro Bruto ÷ Receita Líquida Total × 100 (por categoria)
  21. Receita Loja Física    : Receita Líquida Total onde canal_venda = "Loja Física"
  22. Receita E-commerce     : Receita Líquida Total onde canal_venda = "E-commerce"
  23. Receita Representante  : Receita Líquida Total onde canal_venda = "Representante"
  24. Share Canal %          : Receita do canal selecionado ÷ Receita Líquida Total × 100

GRUPO 5 — Cancelamentos e Perdas
  25. Total Cancelamentos    : contagem distinta de id_venda onde status_venda = "cancelada"
  26. Receita Cancelada      : soma de receita_liquida onde status_venda = "cancelada"
  27. Taxa Cancelamento %    : Total Cancelamentos ÷ DISTINCTCOUNT(fato_vendas[id_venda]) × 100
  28. Total Devoluções       : contagem distinta de id_venda onde status_venda = "devolvida"
  29. Receita Devolvida      : soma de receita_liquida onde status_venda = "devolvida"

Para cada medida, forneça:
  - Nome exato da medida
  - Fórmula DAX completa e comentada
  - Formatação recomendada (moeda BRL, percentual com 1 casa, inteiro, etc.)
  - Tabela de destino sugerida (criar tabela "_Medidas" separada)
```

---

## Paleta de Cores LH Nautical

```
Azul Principal:  #1565C0
Verde Sucesso:   #2E7D32
Laranja Alerta:  #E65100
Cinza Neutro:    #546E7A
Fundo:           #F5F5F5
```








# 🚀 PROMPT — STREAMLIT APP | LH NAUTICAL ANALYTICS PLATFORM

Você é um Engenheiro de Software Full Stack + Especialista em Streamlit + UX/UI Designer focado em Analytics Applications.

Sua missão é criar uma aplicação web profissional em Streamlit para o projeto LH Nautical Analytics Platform.

A aplicação deve parecer um sistema corporativo real de Business Intelligence, Analytics e Inteligência Artificial.

O foco principal NÃO é apenas exibir gráficos, mas criar uma experiência moderna, executiva, organizada e altamente visual.

---

# 🧠 CONTEXTO DO PROJETO

A LH Nautical é uma empresa de varejo de peças e acessórios náuticos que enfrenta problemas graves de organização de dados.

O projeto já possui pipeline de Engenharia de Dados estruturado em arquitetura Medallion:

* RAW
* BRONZE
* SILVER
* GOLD

Os dados finais utilizados pela aplicação estão em:

```python
data/gold/
```

Arquivos disponíveis:

* fato_vendas.parquet
* dim_clientes.parquet
* dim_produtos.parquet

---

# 🎯 OBJETIVO DA APLICAÇÃO

Criar uma plataforma analítica interativa para:

* Diretoria
* Gerência
* Equipe de dados

A aplicação deve permitir:

✅ Visualização executiva
✅ Exploração analítica
✅ Monitoramento de KPIs
✅ Insights de vendas
✅ Análise de clientes
✅ Previsão de demanda
✅ Sistema de recomendação

---

# 🏗️ ESTRUTURA OBRIGATÓRIA DO PROJETO

Criar toda a estrutura abaixo:

/streamlit_app
│
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
│
├── assets/
│   ├── logo.png
│   ├── background.png
│   └── styles.css
│
├── pages/
│   ├── 01_📊_Dashboard_Executivo.py
│   ├── 02_📦_Produtos.py
│   ├── 03_👥_Clientes.py
│   ├── 04_📈_Temporal.py
│   ├── 05_🔮_Previsao.py
│   └── 06_🤖_Recomendacoes.py
│
├── src/
│   ├── data_loader.py
│   ├── metrics.py
│   ├── charts.py
│   ├── filters.py
│   ├── forecasting.py
│   └── recommendation.py
│
└── data/
└── gold/

---

# 🎨 DESIGN E UX/UI

A aplicação deve possuir design moderno estilo:

* Power BI Service
* Tableau
* Stripe Analytics
* Notion Dashboard
* Databricks UI

Utilizar:

✅ Layout responsivo
✅ Sidebar moderna
✅ Cards KPI profissionais
✅ Gráficos interativos
✅ Efeitos suaves
✅ Containers organizados
✅ Visual executivo premium

---

# 🎨 PALETA DE CORES OFICIAL

Utilizar obrigatoriamente:

Azul Principal:  #1565C0
Verde Sucesso:   #2E7D32
Laranja Alerta:  #E65100
Cinza Neutro:    #546E7A
Fundo:           #F5F5F5

---

# ⚡ EXPERIÊNCIA VISUAL

A aplicação deve parecer premium.

Adicionar:

* Hover effects
* KPI cards animados
* Sombras suaves
* Bordas arredondadas
* Ícones
* Métricas destacadas
* Header executivo
* Sidebar elegante
* Containers modernos

Utilizar:

* streamlit-option-menu
* plotly
* streamlit-extras
* CSS customizado

---

# 📊 PÁGINAS OBRIGATÓRIAS

# 1. Dashboard Executivo

Criar:

## KPIs

* Receita Líquida
* Lucro Bruto
* Margem %
* Ticket Médio
* Total de Pedidos

## Visuais

* Evolução mensal de receita
* Receita por canal
* Margem por categoria
* Top produtos
* Top clientes

## Filtros

* Ano
* Mês
* Canal
* Categoria

---

# 2. Produtos

Criar:

* Top produtos por receita
* Produtos com prejuízo
* Margem por produto
* Receita por categoria
* Scatter plot margem × volume

Adicionar alertas visuais:

* Produtos negativos em vermelho

---

# 3. Clientes

Criar:

* Top clientes
* Receita por estado
* Segmentação de clientes
* Frequência de compra
* Mapa geográfico

---

# 4. Temporal

Criar:

* Receita por mês
* Receita acumulada
* Comparação YoY
* Vendas por dia da semana
* Heatmap temporal

---

# 5. Previsão

Implementar:

* Média móvel
* Regressão linear simples
* Projeção futura

Exibir:

* gráfico de previsão
* tendência
* explicação da metodologia

---

# 6. Recomendações

Criar:

* Produtos mais vendidos
* Produtos relacionados
* Recomendação por popularidade
* Produtos frequentemente comprados juntos

---

# 📦 DADOS

A aplicação deve:

* Ler arquivos parquet automaticamente
* Utilizar cache do Streamlit
* Ter carregamento otimizado

Utilizar:

```python
@st.cache_data
```

---

# 📈 KPIs OBRIGATÓRIOS

Implementar métricas equivalentes às medidas DAX:

* Receita Líquida
* Receita Bruta
* Lucro Bruto
* Margem %
* Ticket Médio
* Receita por Canal
* Receita por Categoria
* Cancelamentos
* Devoluções

---

# 📊 GRÁFICOS

Utilizar Plotly.

OBRIGATÓRIO:

* gráficos interativos
* tooltips
* zoom
* hover
* responsividade

---

# 💻 PADRÕES DE CÓDIGO

OBRIGATÓRIO:

✅ Código modular
✅ Funções reutilizáveis
✅ Componentização
✅ Organização profissional
✅ Comentários explicativos
✅ Código limpo

Separar:

* lógica
* visual
* métricas
* carregamento
* filtros

---

# 🚀 PERFORMANCE

Implementar:

* cache
* carregamento otimizado
* lazy loading quando possível

Evitar:

* recarregamento desnecessário
* processamento repetido

---

# 📱 RESPONSIVIDADE

A aplicação deve funcionar bem em:

* notebook
* monitor ultrawide
* telas menores

---

# 🔥 DIFERENCIAIS IMPORTANTES

Adicionar:

* loading spinners
* mensagens executivas
* insights automáticos
* indicadores de crescimento
* badges de performance

---

# 🧠 COMUNICAÇÃO EXECUTIVA

A aplicação deve convencer:

* gestores
* diretoria
* equipe técnica

Os textos devem parecer profissionais e corporativos.

---

# 📘 README

Gerar README completo contendo:

* instalação
* execução
* estrutura
* tecnologias
* prints esperados
* arquitetura

---

# 📦 REQUIREMENTS.TXT

Gerar automaticamente contendo:

* streamlit
* pandas
* plotly
* scikit-learn
* pyarrow
* numpy
* streamlit-option-menu
* streamlit-extras

---

# ⚠️ IMPORTANTE

Gabriel Santos (Tech Lead) valoriza:

* clareza
* arquitetura
* modularização
* legibilidade

Priorize:

* organização
* separação de responsabilidades
* experiência visual
* qualidade da aplicação

Acima de:

* código excessivamente complexo

---

# 🚀 RESULTADO FINAL ESPERADO

A aplicação deve parecer:

✅ Plataforma corporativa real
✅ Sistema premium de analytics
✅ Dashboard executivo moderno
✅ Projeto forte de portfólio
✅ Aplicação pronta para demonstração
✅ Estrutura profissional escalável
✅ Interface visual impressionante

O projeto final deve transmitir maturidade profissional em:

* Engenharia de Dados
* Analytics
* BI
* UX/UI
* Desenvolvimento de aplicações analíticas



O Que o Arquivo Contém
📁 Tabela: medidas
   ├─ 📁 KPIs Financeiros (8)
   │  ├─ Receita Bruta Total
   │  ├─ Receita Liquida Total
   │  ├─ Custo Total
   │  ├─ Lucro Bruto
   │  ├─ Margem Bruta %
   │  ├─ Ticket Medio
   │  ├─ Total Pedidos
   │  └─ Quantidade Total
   │
   ├─ 📁 Temporal (6)
   │  ├─ Receita YTD
   │  ├─ Receita Mes Anterior
   │  ├─ Variacao MoM R$
   │  ├─ Variacao MoM %
   │  ├─ Receita Ano Anterior
   │  └─ Variacao YoY %
   │
   ├─ 📁 Clientes (4)
   │  ├─ Total Clientes Unicos
   │  ├─ Receita por Cliente
   │  ├─ Pedidos por Cliente
   │  └─ Top Cliente Receita
   │
   ├─ 📁 Produtos & Canais (6)
   │  ├─ Receita por Categoria
   │  ├─ Margem por Categoria %
   │  ├─ Receita Loja Fisica
   │  ├─ Receita Ecommerce
   │  ├─ Receita Representante
   │  └─ Share Canal %
   │
   └─ 📁 Riscos (5)
      ├─ Total Cancelamentos
      ├─ Receita Cancelada
      ├─ Taxa Cancelamento %
      ├─ Total Devolucoes
      └─ Receita Devolvida