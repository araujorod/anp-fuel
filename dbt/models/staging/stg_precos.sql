-- Staging: ponte padronizada entre a fonte e os modelos analíticos.
-- Regra: só renomes leves, casts e derivações simples. Nada de agregação.

SELECT
    id,
    revenda,
    cnpj,
    regiao,
    uf,
    cidade,
    bairro,
    produto,
    data_coleta,
    valor_venda,
    bandeira,
    DATE_TRUNC('month', data_coleta)::date AS mes_coleta
FROM {{ source('anp', 'precos_combustiveis') }}