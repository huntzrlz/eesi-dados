select *,
    case when divida_id is null then 'divida_id_ausente' when ocorrencias_divida_id > 1 then 'divida_id_duplicado' when saldo_devedor is null or saldo_devedor <= 0 then 'saldo_invalido' when valor_parcela_mensal is null or valor_parcela_mensal < 0 then 'parcela_invalida' when tipo_credor not in ('banco', 'cartao', 'varejo', 'servico_publico') then 'tipo_credor_invalido' end as motivo_quarentena
from {{ ref('stg_dividas') }}
where not registro_valido or ocorrencias_divida_id > 1

