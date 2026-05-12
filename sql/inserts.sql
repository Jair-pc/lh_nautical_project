-- =============================================================
-- LH Nautical — Inserts de Dados de Referência
-- =============================================================
-- Popula tabelas de dimensão com dados fixos (canais, calendário).
-- Os dados de clientes, produtos e fato_vendas são carregados
-- pelo pipeline Python (src/processing/transform.py).
-- =============================================================


-- -------------------------------------------------------------
-- Dimensão Canal
-- -------------------------------------------------------------
INSERT INTO dim_canal (canal_nome, descricao) VALUES
    ('loja_fisica', 'Loja física de Florianópolis — atendimento presencial'),
    ('ecommerce',   'E-commerce nacional — pedidos via site')
ON CONFLICT (canal_nome) DO NOTHING;


-- -------------------------------------------------------------
-- Dimensão Tempo — sample 2023 e 2024
-- Geração completa deve ser feita via script Python ou CTE recursiva
-- -------------------------------------------------------------

-- CTE para gerar todos os dias de 2023 e 2024
-- (execute em bancos que suportam SQL recursivo: PostgreSQL, DuckDB, SQLite ≥ 3.35)
WITH RECURSIVE calendario AS (
    SELECT DATE('2023-01-01') AS data
    UNION ALL
    SELECT DATE(data, '+1 day')
    FROM calendario
    WHERE data < DATE('2024-12-31')
)
INSERT INTO dim_tempo (
    id_tempo, data, ano, semestre, trimestre, mes, nome_mes,
    semana_ano, dia_mes, dia_semana, nome_dia, e_fim_de_semana, e_alta_temporada
)
SELECT
    CAST(STRFTIME('%Y%m%d', data) AS INTEGER)   AS id_tempo,
    data,
    CAST(STRFTIME('%Y', data) AS INTEGER)        AS ano,
    CASE WHEN CAST(STRFTIME('%m', data) AS INTEGER) <= 6 THEN 1 ELSE 2 END AS semestre,
    CASE
        WHEN CAST(STRFTIME('%m', data) AS INTEGER) BETWEEN 1  AND 3  THEN 1
        WHEN CAST(STRFTIME('%m', data) AS INTEGER) BETWEEN 4  AND 6  THEN 2
        WHEN CAST(STRFTIME('%m', data) AS INTEGER) BETWEEN 7  AND 9  THEN 3
        ELSE 4
    END                                                                     AS trimestre,
    CAST(STRFTIME('%m', data) AS INTEGER)        AS mes,
    CASE STRFTIME('%m', data)
        WHEN '01' THEN 'Janeiro'   WHEN '02' THEN 'Fevereiro'
        WHEN '03' THEN 'Março'     WHEN '04' THEN 'Abril'
        WHEN '05' THEN 'Maio'      WHEN '06' THEN 'Junho'
        WHEN '07' THEN 'Julho'     WHEN '08' THEN 'Agosto'
        WHEN '09' THEN 'Setembro'  WHEN '10' THEN 'Outubro'
        WHEN '11' THEN 'Novembro'  ELSE 'Dezembro'
    END                                          AS nome_mes,
    CAST(STRFTIME('%W', data) AS INTEGER)        AS semana_ano,
    CAST(STRFTIME('%d', data) AS INTEGER)        AS dia_mes,
    CAST(STRFTIME('%w', data) AS INTEGER)        AS dia_semana,  -- 0=Dom, 6=Sáb
    CASE STRFTIME('%A', data)
        WHEN 'Monday'    THEN 'Segunda'   WHEN 'Tuesday'  THEN 'Terça'
        WHEN 'Wednesday' THEN 'Quarta'    WHEN 'Thursday' THEN 'Quinta'
        WHEN 'Friday'    THEN 'Sexta'     WHEN 'Saturday' THEN 'Sábado'
        ELSE 'Domingo'
    END                                          AS nome_dia,
    CASE WHEN STRFTIME('%w', data) IN ('0', '6') THEN 1 ELSE 0 END AS e_fim_de_semana,
    -- Alta temporada náutica: dezembro, janeiro, fevereiro (verão SC) e julho (recesso)
    CASE
        WHEN CAST(STRFTIME('%m', data) AS INTEGER) IN (12, 1, 2, 7) THEN 1
        ELSE 0
    END                                          AS e_alta_temporada
FROM calendario
ON CONFLICT (id_tempo) DO NOTHING;
