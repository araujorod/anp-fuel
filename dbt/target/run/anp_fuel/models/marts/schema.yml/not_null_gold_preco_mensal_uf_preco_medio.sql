
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select preco_medio
from "anp_fuel"."public"."gold_preco_mensal_uf"
where preco_medio is null



  
  
      
    ) dbt_internal_test