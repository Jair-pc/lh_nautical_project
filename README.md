# LH Nautical — Projeto Completo de Dados

> Transformação de dados brutos em uma plataforma analítica profissional com arquitetura Medallion.

## Visão do Projeto

A **LH Nautical** é uma empresa de varejo de peças e acessórios para embarcações,
operando com loja física em Florianópolis e e-commerce nacional. Este projeto
transforma quatro fontes de dados brutas em uma **plataforma analítica completa**
— com pipeline automatizado, métricas financeiras, previsão de demanda e sistema
de recomendação de produtos.

---

## Resultados dos Dados Reais (2023–2024)

| Indicador               | Valor                  |
|-------------------------|------------------------|
| Receita líquida total   | R$ 2,61 bilhões        |
| Lucro bruto             | R$ 99,6 milhões        |
| Margem média            | 3,6%                   |
| Total de pedidos        | 9.895                  |
| Itens vendidos          | 79.311                 |
| Ticket médio/pedido     | R$ 263.797             |
| Clientes únicos         | 49                     |
| Produtos no catálogo    | 150                    |
| E-commerce vs loja fís. | 98% vs 2%              |

**Alertas identificados:**
- 30 produtos com margem negativa acumulada (vendidos abaixo do custo)
- 61% dos e-mails de clientes inválidos — risco crítico para CRM
- Alta concentração: top 5 clientes respondem por ~33% da receita

---

## Arquitetura — Medallion

```
Bronze (bruto) -> Silver (limpo) -> Gold (modelo estrela) -> BI / ML
```

| Camada   | Descrição                                                               |
|----------|-------------------------------------------------------------------------|
| Bronze   | Arquivos originais (.csv / .json). Nunca modificados. Fonte da verdade. |
| Silver   | Dados limpos: datas parseadas, preços convertidos, categorias normalizadas, localização extraída |
| Gold     | Modelo estrela (Kimball): fato_vendas + dim_clientes + dim_produtos. Métricas financeiras pré-calculadas |

---

## Estrutura do Projeto

```
lh_nautical_project/
│
├── data/
│   ├── bronze/                       <- Dados originais (CSV / JSON)
│   │   ├── vendas_2023_2024.csv      <- 9.895 transações
│   │   ├── produtos_raw.csv          <- 157 linhas (150 após dedup)
│   │   ├── clientes_crm.json         <- 49 clientes
│   │   └── custos_importacao.json    <- 150 produtos com histórico USD
│   ├── silver/                       <- Gerado pelo pipeline (Parquet)
│   └── gold/                         <- Gerado pelo pipeline (Parquet)
│
├── notebooks/
│   ├── 01_eda.ipynb                  <- EDA dos dados Bronze (7 problemas identificados)
│   ├── 02_tratamento.ipynb           <- Pipeline Bronze -> Silver -> Gold
│   ├── 03_analise_vendas.ipynb       <- KPIs, faturamento, margens, sazonalidade
│   ├── 04_clientes.ipynb             <- Ranking, geografico, frequencia
│   ├── 05_previsao.ipynb             <- Media Movel + Regressao Linear
│   └── 06_recomendacao.ipynb         <- Popularidade, relacionados, MBA
│
├── sql/
│   ├── create_tables.sql             <- Modelo estrela (DDL)
│   ├── inserts.sql                   <- Dados de referencia
│   └── queries_analiticas.sql        <- 12 queries prontas para BI
│
├── src/
│   ├── ingestion/ingest.py           <- Carrega Bronze (CSV, JSON)
│   ├── processing/transform.py       <- Bronze -> Silver -> Gold
│   ├── analysis/sales_analysis.py    <- KPIs, rankings, sazonalidade
│   ├── forecasting/demand_forecast.py <- Media Movel + Regressao Linear
│   └── recommendation/recommender.py <- Popularidade, relacionados, MBA
│
├── dashboards/
│   └── README_POWERBI.md             <- Guia Power BI + medidas DAX
│
├── main.py                           <- Orquestrador (argparse)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Como Executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Pipeline completo (todas as 5 etapas)
python main.py

# Etapa específica
python main.py --etapa analysis
python main.py --etapa forecast
python main.py --etapa recommendation

# Notebooks (executar na ordem)
jupyter notebook
```

O pipeline completo roda em ~2 segundos e salva os Parquet em `data/silver/` e `data/gold/`.

---

## Problemas de Qualidade Encontrados (EDA)

| # | Dataset  | Problema                                          | Tratamento aplicado              |
|---|----------|---------------------------------------------------|----------------------------------|
| 1 | Vendas   | `sale_date` com 2 formatos (ISO e BR misturados)  | Parse adaptativo                 |
| 2 | Produtos | `price` como string `"R$ X.XXX,XX"`               | Conversão numérica               |
| 3 | Produtos | `actual_category` com ~38 variações gráficas      | Normalização para 3 canônicas    |
| 4 | Produtos | 7 linhas duplicadas (mesmo código)                | `drop_duplicates()`              |
| 5 | Clientes | `location` com 3+ separadores inconsistentes      | Regex para cidade/estado         |
| 6 | Clientes | 30 e-mails inválidos (61% da base)                | Flag `email_valido`              |
| 7 | Custos   | `historic_data` é lista JSON aninhada             | Extração do registro mais recente|

---

## Pipeline de Dados

```
Etapa 1: Ingestion      Bronze carregado (CSV + JSON -> DataFrames)
Etapa 2: Transformation Bronze -> Silver -> Gold
         Silver: datas, precos, categorias, localizacao, deduplicacao
         Gold: join vendas+produtos+clientes+custos, metricas financeiras
Etapa 3: Analysis       KPIs + Relatorio Executivo
Etapa 4: Forecast       Media Movel (3M) + Regressao Linear (6M)
Etapa 5: Recommendation Popularidade + Relacionados + Market Basket
```

---

## Principais Insights

**Margem sob pressão:** 3,6% de margem média com 30 produtos deficitários.
Revisão urgente de precificação para itens vendidos abaixo do custo de importação.

**E-commerce dominante:** 98% da receita via canal digital. Qualquer investimento
de aquisição tem ROI muito superior em marketing digital do que em expansão física.

**Base B2B de alta recorrência:** 49 clientes fazem ~200 pedidos cada no período —
perfil de distribuidores/revendedores. Estratégia de CRM deve ser personalizada por conta.

**Alta concentração:** Top 5 clientes = ~33% da receita. Risco operacional relevante
que justifica diversificação ativa da base.

**Pares para cross-sell:** Produtos 11, 35, 51, 103 e 122 são comprados juntos
por ~77% dos clientes — candidatos prioritários para kits promocionais.

---

## Tecnologias

| Categoria     | Tecnologia             | Uso                                 |
|---------------|------------------------|-------------------------------------|
| Linguagem     | Python 3.11+           | Todo o pipeline                     |
| Dados         | Pandas, NumPy          | Transformação e análise             |
| Armazenamento | Apache Parquet         | Camadas Silver e Gold               |
| ML            | Scikit-Learn           | Regressão linear                    |
| Visualização  | Matplotlib, Seaborn    | Gráficos nos notebooks              |
| SQL           | SQLite / PostgreSQL    | Modelo estrela e queries analíticas |
| BI            | Power BI               | Dashboards executivos               |
| Notebooks     | Jupyter                | EDA e storytelling                  |

---

## Próximos Passos

```
Curto prazo:
  -> Dashboard Power BI conectado aos Parquet do Gold
  -> Corrigir base de e-mails (campanha de atualização cadastral)
  -> Revisão de precificação para os 30 produtos com margem negativa

Médio prazo:
  -> Implementar dbt para transformações Silver -> Gold
  -> Forecasting com Prophet quando houver >= 3 anos de histórico
  -> Filtro colaborativo para recomendações (500+ clientes)

Longo prazo:
  -> Migrar para Databricks (escala)
  -> Previsão de churn de clientes
  -> Otimização de estoque com modelo de reposição automática
```
