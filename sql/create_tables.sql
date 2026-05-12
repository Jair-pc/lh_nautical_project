-- =============================================================
-- LH Nautical — Criação do Modelo Estrela (Star Schema)
-- =============================================================
-- Arquitetura: Data Warehouse camada Gold
-- Padrão:      Kimball Star Schema
--
-- Tabelas:
--   dim_tempo       → calendário analítico
--   dim_clientes    → cadastro e segmentação de clientes
--   dim_produtos    → catálogo de produtos com margens
--   dim_canal       → canais de venda
--   fato_vendas     → transações com métricas financeiras
-- =============================================================


-- -------------------------------------------------------------
-- DIMENSÃO TEMPO
-- Calendário completo com atributos úteis para análise sazonal
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_tempo (
    id_tempo        INTEGER PRIMARY KEY,  -- formato: YYYYMMDD
    data            DATE        NOT NULL,
    ano             SMALLINT    NOT NULL,
    semestre        SMALLINT    NOT NULL,
    trimestre       SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL,
    nome_mes        VARCHAR(15) NOT NULL,
    semana_ano      SMALLINT    NOT NULL,
    dia_mes         SMALLINT    NOT NULL,
    dia_semana      SMALLINT    NOT NULL, -- 0=Segunda ... 6=Domingo
    nome_dia        VARCHAR(15) NOT NULL,
    e_fim_de_semana BOOLEAN     NOT NULL DEFAULT FALSE,
    e_alta_temporada BOOLEAN    NOT NULL DEFAULT FALSE  -- dez-fev e jul (náutico)
);

-- Índice para buscas por período
CREATE INDEX IF NOT EXISTS idx_tempo_ano_mes ON dim_tempo (ano, mes);


-- -------------------------------------------------------------
-- DIMENSÃO CLIENTES
-- Dados cadastrais e segmento de mercado do cliente
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_clientes (
    id_cliente      VARCHAR(10)  PRIMARY KEY,
    nome_completo   VARCHAR(120) NOT NULL,
    email           VARCHAR(120),
    email_valido    BOOLEAN      DEFAULT TRUE,
    cidade          VARCHAR(80),
    estado          CHAR(2),
    segmento_cliente VARCHAR(40),  -- pescador_amador, vela_esportiva, etc.
    canal_aquisicao VARCHAR(20),   -- como o cliente chegou à LH Nautical
    data_cadastro   DATE,
    ativo           BOOLEAN      DEFAULT TRUE,
    criado_em       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cli_estado ON dim_clientes (estado);
CREATE INDEX IF NOT EXISTS idx_cli_segmento ON dim_clientes (segmento_cliente);


-- -------------------------------------------------------------
-- DIMENSÃO PRODUTOS
-- Catálogo com informações de custo, preço e margem
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_produtos (
    id_produto          VARCHAR(10)  PRIMARY KEY,
    sku                 VARCHAR(30)  UNIQUE,
    nome_produto        VARCHAR(150) NOT NULL,
    categoria           VARCHAR(60)  NOT NULL,
    subcategoria        VARCHAR(60),
    preco_custo         NUMERIC(12, 2),
    preco_venda         NUMERIC(12, 2),
    margem_unitaria_pct NUMERIC(6, 2),  -- (venda - custo) / venda × 100
    estoque_atual       INTEGER      DEFAULT 0,
    fornecedor          VARCHAR(80),
    unidade             VARCHAR(20),
    ativo               BOOLEAN      DEFAULT TRUE,
    criado_em           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prod_categoria ON dim_produtos (categoria);


-- -------------------------------------------------------------
-- DIMENSÃO CANAL DE VENDA
-- Separa as operações entre loja física e e-commerce
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_canal (
    id_canal    SERIAL      PRIMARY KEY,
    canal_nome  VARCHAR(30) UNIQUE NOT NULL,  -- loja_fisica | ecommerce
    descricao   VARCHAR(120)
);


-- -------------------------------------------------------------
-- TABELA FATO VENDAS
-- Grão: uma linha por item de uma transação de venda
-- Métricas financeiras pré-calculadas para performance em BI
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fato_vendas (
    id_fato         BIGSERIAL    PRIMARY KEY,
    id_venda        VARCHAR(10)  NOT NULL,
    id_tempo        INTEGER      REFERENCES dim_tempo(id_tempo),
    id_cliente      VARCHAR(10)  REFERENCES dim_clientes(id_cliente),
    id_produto      VARCHAR(10)  REFERENCES dim_produtos(id_produto),
    id_canal        INTEGER      REFERENCES dim_canal(id_canal),
    status_venda    VARCHAR(20)  NOT NULL,

    -- Métricas de volume
    quantidade      INTEGER      NOT NULL,
    preco_unitario  NUMERIC(12, 2) NOT NULL,
    desconto_pct    NUMERIC(5, 2)  DEFAULT 0,

    -- Métricas financeiras derivadas (pré-calculadas para performance)
    receita_bruta   NUMERIC(14, 2),  -- qtd × preco_unitario
    desconto_valor  NUMERIC(14, 2),  -- receita_bruta × desconto_pct/100
    receita_liquida NUMERIC(14, 2),  -- receita_bruta - desconto_valor
    custo_total     NUMERIC(14, 2),  -- qtd × custo_unitario do produto
    lucro_bruto     NUMERIC(14, 2),  -- receita_liquida - custo_total
    margem_pct      NUMERIC(6, 2),   -- lucro_bruto / receita_liquida × 100

    criado_em       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- Índices para as queries analíticas mais comuns
CREATE INDEX IF NOT EXISTS idx_fato_tempo    ON fato_vendas (id_tempo);
CREATE INDEX IF NOT EXISTS idx_fato_cliente  ON fato_vendas (id_cliente);
CREATE INDEX IF NOT EXISTS idx_fato_produto  ON fato_vendas (id_produto);
CREATE INDEX IF NOT EXISTS idx_fato_canal    ON fato_vendas (id_canal);
CREATE INDEX IF NOT EXISTS idx_fato_status   ON fato_vendas (status_venda);
CREATE INDEX IF NOT EXISTS idx_fato_venda_id ON fato_vendas (id_venda);


-- -------------------------------------------------------------
-- VIEW: vw_vendas_completas
-- Desnormaliza fato + dimensões para facilitar consultas rápidas
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vw_vendas_completas AS
SELECT
    fv.id_venda,
    dt.data,
    dt.ano,
    dt.mes,
    dt.nome_mes,
    dt.trimestre,
    dt.nome_dia,
    dt.e_alta_temporada,
    dc.nome_completo    AS cliente_nome,
    dc.cidade           AS cliente_cidade,
    dc.estado           AS cliente_estado,
    dc.segmento_cliente,
    dp.nome_produto,
    dp.categoria,
    dp.subcategoria,
    dca.canal_nome      AS canal_venda,
    fv.status_venda,
    fv.quantidade,
    fv.preco_unitario,
    fv.desconto_pct,
    fv.receita_bruta,
    fv.receita_liquida,
    fv.custo_total,
    fv.lucro_bruto,
    fv.margem_pct
FROM fato_vendas fv
LEFT JOIN dim_tempo     dt  ON fv.id_tempo   = dt.id_tempo
LEFT JOIN dim_clientes  dc  ON fv.id_cliente = dc.id_cliente
LEFT JOIN dim_produtos  dp  ON fv.id_produto = dp.id_produto
LEFT JOIN dim_canal     dca ON fv.id_canal   = dca.id_canal;
