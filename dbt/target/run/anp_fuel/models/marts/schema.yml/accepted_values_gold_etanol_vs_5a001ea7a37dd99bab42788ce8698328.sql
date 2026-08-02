
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        combustivel_vantajoso as value_field,
        count(*) as n_records

    from "anp_fuel"."public"."gold_etanol_vs_gasolina"
    group by combustivel_vantajoso

)

select *
from all_values
where value_field not in (
    'ETANOL','GASOLINA'
)



  
  
      
    ) dbt_internal_test