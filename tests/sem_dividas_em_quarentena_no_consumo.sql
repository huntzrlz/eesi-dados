select f.divida_id from {{ ref('fct_divida_servidor') }} f join {{ ref('quarentena_dividas') }} q using (divida_id)
