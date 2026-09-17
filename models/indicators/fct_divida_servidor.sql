-- Uma linha por dívida válida, servidor e mês de referência.
with dividas_unicas as (
    select *, row_number() over (partition by divida_id order by capturado_em) as ordem
    from {{ ref('stg_dividas') }}
    where registro_valido
), formularios_validos as (
    select * from {{ ref('stg_formularios') }} where registro_valido
)
select
    d.divida_id, d.servidor_id, f.mes_referencia, f.secretaria_municipal,
    d.credor, d.tipo_credor, d.saldo_devedor, d.valor_parcela_mensal,
    f.renda_liquida, f.despesa_basica
from dividas_unicas d
join formularios_validos f using (servidor_id)
where d.ordem = 1

