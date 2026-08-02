-- Dimensão posto: uma linha por CNPJ (estabelecimento revendedor).

SELECT
    {{ dbt_utils.generate_surrogate_key(['cnpj']) }} AS sk_posto,
    cnpj,
    MAX(revenda)  AS revenda,
    MAX(bandeira) AS bandeira,
    MAX(uf)       AS uf,
    MAX(cidade)   AS cidade,
    MAX(bairro)   AS bairro
FROM {{ ref('stg_precos') }}
GROUP BY cnpj