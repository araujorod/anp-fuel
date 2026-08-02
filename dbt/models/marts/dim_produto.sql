-- dim_produto.sql

SELECT
    {{ dbt_utils.generate_surrogate_key(['produto']) }} AS sk_produto,
    produto,
    MAX(unidade_medida) AS unidade_medida
FROM {{ ref('stg_precos') }}
GROUP BY produto