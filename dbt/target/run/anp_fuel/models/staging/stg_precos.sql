
  create view "anp_fuel"."public"."stg_precos__dbt_tmp"
    
    
  as (
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
    unidade_medida,
    bandeira,
    DATE_TRUNC('month', data_coleta)::date AS mes_coleta
FROM "anp_fuel"."public"."precos_combustiveis"
  );