
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select uf
from "anp_fuel"."public"."stg_precos"
where uf is null



  
  
      
    ) dbt_internal_test