-- Uma linha por dívida válida, servidor e mês de referência.
-- Excluímos todas as ocorrências duplicadas: não há evidência para escolher a correta.
-- O join exige formulário válido para não atribuir renda inválida a uma dívida.
with dividas_unicas as (
    select *
    from {{ ref('stg_dividas') }}
    where registro_valido and ocorrencias_divida_id = 1
), formularios_validos as (
    select * from {{ ref('stg_formularios') }} where registro_valido
)
select
    d.divida_id, d.servidor_id, f.mes_referencia, f.secretaria_municipal,
    d.credor, d.tipo_credor, d.saldo_devedor, d.valor_parcela_mensal,
    f.renda_liquida, f.despesa_basica
from dividas_unicas d
join formularios_validos f using (servidor_id)
