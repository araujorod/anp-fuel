-- Dimensão tempo: uma linha por data presente na série.

SELECT DISTINCT
    {{ dbt_utils.generate_surrogate_key(['data_coleta']) }} AS sk_tempo,
    data_coleta,
    EXTRACT(YEAR    FROM data_coleta)::int  AS ano,
    EXTRACT(MONTH   FROM data_coleta)::int  AS mes,
    EXTRACT(QUARTER FROM data_coleta)::int  AS trimestre,
    CASE WHEN EXTRACT(MONTH FROM data_coleta) <= 6 THEN 1 ELSE 2 END AS semestre,
    TO_CHAR(data_coleta, 'TMMonth')         AS nome_mes,
    EXTRACT(ISODOW FROM data_coleta)::int   AS dia_semana
FROM {{ ref('stg_precos') }}