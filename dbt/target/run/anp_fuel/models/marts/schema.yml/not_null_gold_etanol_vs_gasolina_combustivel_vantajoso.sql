
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select combustivel_vantajoso
from "anp_fuel"."public"."gold_etanol_vs_gasolina"
where combustivel_vantajoso is null



  
  
      
    ) dbt_internal_test