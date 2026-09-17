with origem as (
    select * from {{ source('bronze', 'bronze_dividas') }}
), tipado as (
    select
        trim(divida_id) as divida_id,
        trim(servidor_id) as servidor_id,
        trim(credor) as credor,
        case lower(trim(tipo_credor)) when 'cartão' then 'cartao' else lower(trim(tipo_credor)) end as tipo_credor,
        case when strpos(saldo_devedor, ',') > 0 then try_cast(replace(replace(replace(saldo_devedor, 'R$', ''), '.', ''), ',', '.') as decimal(18,2)) else try_cast(replace(replace(saldo_devedor, 'R$', ''), ' ', '') as decimal(18,2)) end as saldo_devedor,
        case when strpos(valor_parcela_mensal, ',') > 0 then try_cast(replace(replace(replace(valor_parcela_mensal, 'R$', ''), '.', ''), ',', '.') as decimal(18,2)) else try_cast(replace(replace(valor_parcela_mensal, 'R$', ''), ' ', '') as decimal(18,2)) end as valor_parcela_mensal,
        try_cast(qtd_parcelas as integer) as qtd_parcelas,
        arquivo_origem, lote, capturado_em
    from origem
)
select *,
    count(*) over (partition by divida_id) as ocorrencias_divida_id,
    case when divida_id is not null and servidor_id is not null and saldo_devedor > 0 and valor_parcela_mensal >= 0 and tipo_credor in ('banco', 'cartao', 'varejo', 'servico_publico') then true else false end as registro_valido
from tipado

