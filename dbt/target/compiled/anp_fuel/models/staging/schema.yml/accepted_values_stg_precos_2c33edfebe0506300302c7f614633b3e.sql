
    
    

with all_values as (

    select
        produto as value_field,
        count(*) as n_records

    from "anp_fuel"."public"."stg_precos"
    group by produto

)

select *
from all_values
where value_field not in (
    'GASOLINA','GASOLINA ADITIVADA','ETANOL','DIESEL','DIESEL S10','GNV'
)


