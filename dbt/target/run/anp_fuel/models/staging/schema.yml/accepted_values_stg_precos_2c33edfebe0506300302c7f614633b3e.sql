
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

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



  
  
      
    ) dbt_internal_test