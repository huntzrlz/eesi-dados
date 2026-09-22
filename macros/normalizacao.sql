{% macro moeda(coluna) -%}
{# Mantém centavos em Decimal; formatos irrecuperáveis viram NULL para quarentena. #}
toDecimal64OrNull(
    if(position({{ coluna }}, ',') > 0,
       replaceAll(replaceAll(replaceAll(replaceAll({{ coluna }}, 'R$', ''), ' ', ''), '.', ''), ',', '.'),
       replaceAll(replaceAll({{ coluna }}, 'R$', ''), ' ', '')),
    2)
{%- endmacro %}

{% macro data_referencia(coluna) -%}
{# Round-trip rejeita datas normalizadas silenciosamente (ex.: 30 de fevereiro). #}
coalesce(
{% for formato in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'] %}
    if(formatDateTime(parseDateTimeOrNull({{ coluna }}, '{{ formato }}'), '{{ formato }}') = {{ coluna }},
       toDate(parseDateTimeOrNull({{ coluna }}, '{{ formato }}')), NULL){% if not loop.last %},{% endif %}
{% endfor %}
)
{%- endmacro %}
