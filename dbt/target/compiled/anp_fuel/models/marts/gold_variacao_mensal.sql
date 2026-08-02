-- Variação percentual do preço médio mês a mês, por UF e produto.
-- Exercita: LAG (comparação com o período anterior).

WITH mensal AS (
    SELECT
        uf,
        produto,
        mes_coleta,
        AVG(valor_venda) AS preco_medio
    FROM "anp_fuel"."public"."stg_precos"
    GROUP BY uf, produto, mes_coleta
)

SELECT
    uf,
    produto,
    mes_coleta,
    ROUND(preco_medio, 3) AS preco_medio,
    ROUND(
        100.0 * (preco_medio - LAG(preco_medio) OVER w) / LAG(preco_medio) OVER w,
        2
    ) AS variacao_pct
FROM mensal
WINDOW w AS (PARTITION BY uf, produto ORDER BY mes_coleta)