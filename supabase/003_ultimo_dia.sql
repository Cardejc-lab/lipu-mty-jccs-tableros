-- Último día cargado por tabla (solo fechas, sin datos de operadores).
-- La usa scripts/exportar_tabla_access.py para exportar solo lo nuevo (carga diferencial).
create or replace function public.lipu_ultimo_dia()
returns table (tabla text, ultimo_dia date)
language sql stable security definer set search_path = public as $$
  select 'TABLA DE VIAJES TL', (select max(inicio_recorrido)::date from base_viajes)
  union all select 'TABLA DE EVENTOS TL', (select max(hora_inicio)::date from base_eventos)
$$;
revoke all on function public.lipu_ultimo_dia() from public;
grant execute on function public.lipu_ultimo_dia() to anon, authenticated;
