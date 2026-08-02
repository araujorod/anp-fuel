
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select produto
from "anp_fuel"."public"."stg_precos"
where produto is null



  
  
      
    ) dbt_internal_test