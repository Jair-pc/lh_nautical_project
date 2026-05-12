-- =============================================================
-- LH Nautical — Queries Analíticas
-- =============================================================
-- Conjunto de consultas SQL prontas para uso em BI e relatórios.
-- Organizadas por tema: Vendas, Produtos, Clientes, Temporal.
--
-- Todas as queries assumem que a view vw_vendas_completas existe
-- e que apenas vendas com status 'concluida' são consideradas.
-- =============================================================


-- =============================================================
-- BLOCO 1: VISÃO GERAL DO NEGÓCIO (KPIs Executivos)
-- Para o Sr. Almir e reuniões de diretoria
-- =============================================================

-- 1.1 KPIs do período completo
SELECT
    COUNT(DISTINCT id_venda)        AS total_pedidos,
    SUM(quantidade)                 AS total_itens_vendidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_liquida_total,
    ROUND(SUM(lucro_bruto), 2)      AS lucro_bruto_total,
    ROUND(AVG(margem_pct), 2)       AS margem_media_pct,
    ROUND(AVG(receita_liquida), 2)  AS ticket_medio
FROM vw_vendas_completas
WHERE status_venda = 'concluida';


-- 1.2 Evolução mensal de receita (para gráfico de linha)
SELECT
    ano,
    mes,
    nome_mes,
    ROUND(SUM(receita_liquida), 2)              AS receita_liquida,
    ROUND(SUM(lucro_bruto), 2)                  AS lucro_bruto,
    COUNT(DISTINCT id_venda)                    AS num_pedidos,
    ROUND(
        (SUM(receita_liquida) - LAG(SUM(receita_liquida)) OVER (ORDER BY ano, mes))
        / NULLIF(LAG(SUM(receita_liquida)) OVER (ORDER BY ano, mes), 0) * 100, 2
    )                                           AS variacao_mom_pct  -- month-over-month
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY ano, mes, nome_mes
ORDER BY ano, mes;


-- 1.3 Comparativo 2023 vs 2024
SELECT
    ano,
    ROUND(SUM(receita_liquida), 2)  AS receita_liquida,
    ROUND(SUM(lucro_bruto), 2)      AS lucro_bruto,
    ROUND(AVG(margem_pct), 2)       AS margem_pct,
    COUNT(DISTINCT id_venda)        AS num_pedidos
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY ano
ORDER BY ano;


-- =============================================================
-- BLOCO 2: ANÁLISE DE PRODUTOS
-- Para Marina Costa (Gerente de Negócios)
-- =============================================================

-- 2.1 Ranking de produtos por receita líquida
SELECT
    id_produto,
    nome_produto,
    categoria,
    SUM(quantidade)                 AS itens_vendidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_liquida,
    ROUND(SUM(lucro_bruto), 2)      AS lucro_bruto,
    ROUND(AVG(margem_pct), 2)       AS margem_pct,
    COUNT(DISTINCT id_venda)        AS num_transacoes
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY id_produto, nome_produto, categoria
ORDER BY receita_liquida DESC
LIMIT 15;


-- 2.2 Produtos com prejuízo acumulado (alerta de gestão)
SELECT
    id_produto,
    nome_produto,
    categoria,
    SUM(quantidade)                 AS itens_vendidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_liquida,
    ROUND(SUM(lucro_bruto), 2)      AS lucro_bruto,
    ROUND(AVG(margem_pct), 2)       AS margem_pct
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY id_produto, nome_produto, categoria
HAVING SUM(lucro_bruto) < 0
ORDER BY lucro_bruto ASC;


-- 2.3 Margem média por categoria
SELECT
    categoria,
    COUNT(DISTINCT id_produto)      AS num_produtos,
    SUM(quantidade)                 AS itens_vendidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_liquida,
    ROUND(SUM(lucro_bruto), 2)      AS lucro_bruto,
    ROUND(AVG(margem_pct), 2)       AS margem_media_pct
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY categoria
ORDER BY receita_liquida DESC;


-- 2.4 Mix de vendas por canal e categoria
SELECT
    canal_venda,
    categoria,
    ROUND(SUM(receita_liquida), 2)                    AS receita,
    ROUND(
        SUM(receita_liquida) * 100.0 /
        SUM(SUM(receita_liquida)) OVER (PARTITION BY canal_venda),
    2)                                                AS share_no_canal_pct
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY canal_venda, categoria
ORDER BY canal_venda, receita DESC;


-- =============================================================
-- BLOCO 3: ANÁLISE DE CLIENTES
-- =============================================================

-- 3.1 Ranking de clientes por valor total (LTV simplificado)
SELECT
    id_venda AS id_cliente,  -- usando alias para clareza no resultado
    cliente_nome,
    cliente_estado,
    segmento_cliente,
    COUNT(DISTINCT id_venda)        AS num_compras,
    SUM(quantidade)                 AS itens_comprados,
    ROUND(SUM(receita_liquida), 2)  AS receita_total,
    ROUND(SUM(lucro_bruto), 2)      AS lucro_gerado,
    ROUND(AVG(receita_liquida), 2)  AS ticket_medio
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY id_venda, cliente_nome, cliente_estado, segmento_cliente
ORDER BY receita_total DESC
LIMIT 10;


-- 3.2 Distribuição geográfica de receita
SELECT
    cliente_estado                  AS estado,
    COUNT(DISTINCT cliente_nome)    AS num_clientes,
    COUNT(DISTINCT id_venda)        AS num_pedidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_total,
    ROUND(AVG(receita_liquida), 2)  AS ticket_medio
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY cliente_estado
ORDER BY receita_total DESC;


-- 3.3 Segmentação de clientes por segmento
SELECT
    segmento_cliente,
    COUNT(DISTINCT cliente_nome)    AS num_clientes,
    COUNT(DISTINCT id_venda)        AS num_pedidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_total,
    ROUND(AVG(receita_liquida), 2)  AS ticket_medio
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY segmento_cliente
ORDER BY receita_total DESC;


-- =============================================================
-- BLOCO 4: ANÁLISE TEMPORAL E SAZONALIDADE
-- =============================================================

-- 4.1 Vendas por dia da semana
SELECT
    nome_dia                        AS dia_semana,
    COUNT(DISTINCT id_venda)        AS num_pedidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_total,
    ROUND(AVG(receita_liquida), 2)  AS ticket_medio
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY nome_dia
ORDER BY
    CASE nome_dia
        WHEN 'Monday'    THEN 1
        WHEN 'Tuesday'   THEN 2
        WHEN 'Wednesday' THEN 3
        WHEN 'Thursday'  THEN 4
        WHEN 'Friday'    THEN 5
        WHEN 'Saturday'  THEN 6
        WHEN 'Sunday'    THEN 7
    END;


-- 4.2 Alta temporada vs Baixa temporada
SELECT
    CASE WHEN e_alta_temporada THEN 'Alta Temporada' ELSE 'Baixa Temporada' END AS periodo,
    COUNT(DISTINCT id_venda)        AS num_pedidos,
    ROUND(SUM(receita_liquida), 2)  AS receita_total,
    ROUND(AVG(receita_liquida), 2)  AS ticket_medio,
    ROUND(AVG(margem_pct), 2)       AS margem_media
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY e_alta_temporada
ORDER BY e_alta_temporada DESC;


-- 4.3 Distribuição por canal de venda
SELECT
    canal_venda,
    COUNT(DISTINCT id_venda)                            AS num_pedidos,
    ROUND(SUM(receita_liquida), 2)                      AS receita_total,
    ROUND(
        SUM(receita_liquida) * 100.0 / SUM(SUM(receita_liquida)) OVER (),
    2)                                                  AS share_pct,
    ROUND(AVG(margem_pct), 2)                           AS margem_media
FROM vw_vendas_completas
WHERE status_venda = 'concluida'
GROUP BY canal_venda
ORDER BY receita_total DESC;
