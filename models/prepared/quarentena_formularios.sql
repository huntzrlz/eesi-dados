select *,
    case when servidor_id is null then 'servidor_id_ausente' when mes_referencia is null then 'mes_referencia_invalido' when renda_liquida is null or renda_liquida <= 0 then 'renda_invalida' when despesa_basica is null or despesa_basica < 0 then 'despesa_basica_invalida' end as motivo_quarentena
from {{ ref('stg_formularios') }}
where not registro_valido

