with origem as (
    select * from {{ source('bronze', 'bronze_formularios') }}
), tipado as (
    select
        trim(servidor_id) as servidor_id,
        coalesce(try_strptime(mes_referencia, '%Y-%m-%d'), try_strptime(mes_referencia, '%d/%m/%Y'), try_strptime(mes_referencia, '%Y/%m/%d'))::date as mes_referencia,
        translate(upper(trim(secretaria_municipal)), 'ÁÀÃÂÉÊÍÓÔÕÚÜÇ', 'AAAAEEIOOOUUC') as secretaria_municipal,
        case when strpos(renda_liquida, ',') > 0 then try_cast(replace(replace(replace(renda_liquida, 'R$', ''), '.', ''), ',', '.') as decimal(18,2)) else try_cast(replace(replace(renda_liquida, 'R$', ''), ' ', '') as decimal(18,2)) end as renda_liquida,
        case when strpos(despesa_basica_informada, ',') > 0 then try_cast(replace(replace(replace(despesa_basica_informada, 'R$', ''), '.', ''), ',', '.') as decimal(18,2)) else try_cast(replace(replace(despesa_basica_informada, 'R$', ''), ' ', '') as decimal(18,2)) end as despesa_basica,
        arquivo_origem, lote, capturado_em
    from origem
)
select *,
    case when servidor_id is not null and mes_referencia is not null and renda_liquida > 0 and despesa_basica >= 0 then true else false end as registro_valido
from tipado
