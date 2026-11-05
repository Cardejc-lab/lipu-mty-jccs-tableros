-- Ventana de detalle (2 meses) + histórico resumido por día · Lipu Monterrey
-- El detalle vive en base_viajes / base_eventos; lo que sale de la ventana se resume aquí antes de borrarse.

create table if not exists public.resumen_viajes_dia (
  fecha date not null,
  num_economico text not null default '',
  id_colaborador text not null default '',
  grupo_vehiculos text not null default '',
  viajes integer not null,
  kms numeric,
  combustible numeric,
  minutos_manejo numeric,
  minutos_ralenti numeric,
  primary key (fecha, num_economico, id_colaborador, grupo_vehiculos)
);

create table if not exists public.resumen_eventos_dia (
  fecha date not null,
  num_economico text not null default '',
  nomina text not null default '',
  grupo_vehiculos text not null default '',
  tipo_evento text not null default '',
  clasificacion text not null default '',
  severidad text not null default '',
  eventos integer not null,
  peso_total numeric,
  primary key (fecha, num_economico, nomina, grupo_vehiculos, tipo_evento, clasificacion, severidad)
);

do $$ declare t text; begin
  foreach t in array array['resumen_viajes_dia','resumen_eventos_dia'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists "Lectura usuarios con sesion" on public.%I', t);
    execute format('create policy "Lectura usuarios con sesion" on public.%I for select to authenticated using (true)', t);
  end loop; end $$;

create index if not exists base_viajes_inicio_idx on public.base_viajes (inicio_recorrido);
create index if not exists base_eventos_inicio_idx on public.base_eventos (hora_inicio);

-- «hh:mm:ss» → minutos
create or replace function public.lipu_minutos(t text) returns numeric language sql immutable as $$
  select case when t ~ '^\d{1,3}:\d{2}(:\d{2})?$'
    then split_part(t, ':', 1)::numeric * 60 + split_part(t, ':', 2)::numeric + coalesce(nullif(split_part(t, ':', 3), '')::numeric, 0) / 60
  end $$;

-- Resume y borra el detalle anterior a «dias» días. Solo el administrador puede ejecutarla.
create or replace function public.lipu_cerrar_ventana(dias integer default 62)
returns table (tabla text, filas_resumidas bigint, filas_borradas bigint)
language plpgsql security definer set search_path = public as $$
declare corte date := (now() at time zone 'America/Mexico_City')::date - dias; nv bigint; ne bigint; bv bigint; be bigint;
begin
  if lower(coalesce(auth.jwt() ->> 'email', '')) <> 'cardejc@live.com' then
    raise exception 'Solo el administrador puede cerrar la ventana';
  end if;

  insert into resumen_viajes_dia as r (fecha, num_economico, id_colaborador, grupo_vehiculos, viajes, kms, combustible, minutos_manejo, minutos_ralenti)
  select inicio_recorrido::date, coalesce(num_economico, ''), coalesce(id_colaborador, ''), coalesce(grupo_vehiculos, ''),
         count(*), sum(kms_viaje), sum(combustible), sum(lipu_minutos(tiempo_manejo)), sum(lipu_minutos(ralenti))
  from base_viajes where inicio_recorrido < corte group by 1, 2, 3, 4
  on conflict (fecha, num_economico, id_colaborador, grupo_vehiculos) do update
    set viajes = excluded.viajes, kms = excluded.kms, combustible = excluded.combustible,
        minutos_manejo = excluded.minutos_manejo, minutos_ralenti = excluded.minutos_ralenti;
  get diagnostics nv = row_count;
  delete from base_viajes where inicio_recorrido < corte; get diagnostics bv = row_count;

  insert into resumen_eventos_dia as r (fecha, num_economico, nomina, grupo_vehiculos, tipo_evento, clasificacion, severidad, eventos, peso_total)
  select hora_inicio::date, coalesce(num_economico, ''), coalesce(nomina, ''), coalesce(grupo_vehiculos, ''),
         coalesce(tipo_evento, ''), coalesce(clasificacion, ''), coalesce(severidad, ''), count(*), sum(peso)
  from base_eventos where hora_inicio < corte group by 1, 2, 3, 4, 5, 6, 7
  on conflict (fecha, num_economico, nomina, grupo_vehiculos, tipo_evento, clasificacion, severidad) do update
    set eventos = excluded.eventos, peso_total = excluded.peso_total;
  get diagnostics ne = row_count;
  delete from base_eventos where hora_inicio < corte; get diagnostics be = row_count;

  return query values ('base_viajes', nv, bv), ('base_eventos', ne, be);
end $$;
revoke all on function public.lipu_cerrar_ventana(integer) from public, anon;
grant execute on function public.lipu_cerrar_ventana(integer) to authenticated;

select 'ok' as estado;
