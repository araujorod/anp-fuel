-- Participação de cada bandeira no total de coletas, por UF.
-- Exercita: window functions (participação percentual e ranking).

SELECT
    uf,
    bandeira,
    COUNT(*)                                          AS qtd_coletas,
    COUNT(DISTINCT cnpj)                              AS qtd_postos,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY uf),
        2
    )                                                 AS participacao_pct,
    RANK() OVER (PARTITION BY uf ORDER BY COUNT(*) DESC) AS posicao
FROM "anp_fuel"."public"."stg_precos"
GROUP BY uf, bandeira