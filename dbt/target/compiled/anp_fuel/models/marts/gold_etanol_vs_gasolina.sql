-- Compara preço médio mensal de etanol e gasolina por UF e aplica a
-- regra dos 70%: etanol compensa se custar até 70% da gasolina
-- (por render ~30% menos por litro).

WITH precos_mensais AS (
    SELECT
        uf,
        mes_coleta,
        produto,
        AVG(valor_venda) AS preco_medio
    FROM "anp_fuel"."public"."stg_precos"
    WHERE produto IN ('ETANOL', 'GASOLINA')
    GROUP BY uf, mes_coleta, produto
),

pivotado AS (
    SELECT
        uf,
        mes_coleta,
        MAX(CASE WHEN produto = 'ETANOL'   THEN preco_medio END) AS preco_etanol,
        MAX(CASE WHEN produto = 'GASOLINA' THEN preco_medio END) AS preco_gasolina
    FROM precos_mensais
    GROUP BY uf, mes_coleta
)

SELECT
    uf,
    mes_coleta,
    ROUND(preco_etanol, 3)                       AS preco_etanol,
    ROUND(preco_gasolina, 3)                     AS preco_gasolina,
    ROUND(preco_etanol / preco_gasolina, 4)      AS razao_etanol_gasolina,
    CASE
        WHEN preco_etanol / preco_gasolina <= 0.70 THEN 'ETANOL'
        ELSE 'GASOLINA'
    END                                          AS combustivel_vantajoso
FROM pivotado
WHERE preco_etanol IS NOT NULL
  AND preco_gasolina IS NOT NULL