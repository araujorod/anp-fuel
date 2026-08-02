-- Preço médio mensal por UF e produto — tabela pronta para análise/dashboard.

SELECT
    uf,
    produto,
    mes_coleta,
    ROUND(AVG(valor_venda), 3) AS preco_medio,
    MIN(valor_venda)           AS preco_min,
    MAX(valor_venda)           AS preco_max,
    COUNT(*)                   AS qtd_coletas
FROM {{ ref('stg_precos') }}
GROUP BY uf, produto, mes_coleta