-- Fato: uma linha por coleta de preço (grão: posto × produto × data).

SELECT
    {{ dbt_utils.generate_surrogate_key(['s.cnpj']) }}        AS sk_posto,
    {{ dbt_utils.generate_surrogate_key(['s.produto']) }}     AS sk_produto,
    {{ dbt_utils.generate_surrogate_key(['s.data_coleta']) }} AS sk_tempo,
    s.valor_venda
FROM {{ ref('stg_precos') }} s