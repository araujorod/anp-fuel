
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select valor_venda
from "anp_fuel"."public"."stg_precos"
where valor_venda is null



  
  
      
    ) dbt_internal_test