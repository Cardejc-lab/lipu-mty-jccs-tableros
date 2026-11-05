-- Recarga de base_viajes y base_eventos desde el Access con ventana de 2 meses · Lipu Monterrey
-- 1) Resume lo anterior a la ventana del archivo (03/09/2026) y vacía el detalle para recargarlo completo.

insert into public.resumen_viajes_dia (fecha, num_economico, id_colaborador, grupo_vehiculos, viajes, kms, combustible, minutos_manejo, minutos_ralenti)
select inicio_recorrido::date, coalesce(num_economico, ''), coalesce(id_colaborador, ''), coalesce(grupo_vehiculos, ''),
       count(*), sum(kms_viaje), sum(combustible), sum(public.lipu_minutos(tiempo_manejo)), sum(public.lipu_minutos(ralenti))
from public.base_viajes where inicio_recorrido < '2026-09-03' group by 1, 2, 3, 4
on conflict (fecha, num_economico, id_colaborador, grupo_vehiculos) do update
  set viajes = excluded.viajes, kms = excluded.kms, combustible = excluded.combustible,
      minutos_manejo = excluded.minutos_manejo, minutos_ralenti = excluded.minutos_ralenti;

insert into public.resumen_eventos_dia (fecha, num_economico, nomina, grupo_vehiculos, tipo_evento, clasificacion, severidad, eventos, peso_total)
select hora_inicio::date, coalesce(num_economico, ''), coalesce(nomina, ''), coalesce(grupo_vehiculos, ''),
       coalesce(tipo_evento, ''), coalesce(clasificacion, ''), coalesce(severidad, ''), count(*), sum(peso)
from public.base_eventos where hora_inicio < '2026-09-03' group by 1, 2, 3, 4, 5, 6, 7
on conflict (fecha, num_economico, nomina, grupo_vehiculos, tipo_evento, clasificacion, severidad) do update
  set eventos = excluded.eventos, peso_total = excluded.peso_total;

truncate table public.base_viajes restart identity;
truncate table public.base_eventos restart identity;

-- 2) Al cargar eventos: clasificación, severidad y peso desde catalogo_eventos; nómina desde catalogo_operadores (nombre exacto)
create or replace function public.lipu_completar_evento() returns trigger language plpgsql as $$
begin
  if new.clasificacion is null or new.severidad is null or new.peso is null then
    select coalesce(new.clasificacion, c.clasificacion), coalesce(new.severidad, c.severidad), coalesce(new.peso, c.peso)
      into new.clasificacion, new.severidad, new.peso
      from public.catalogo_eventos c where c.tipo_evento = new.tipo_evento limit 1;
  end if;
  if new.nomina is null and new.nombre_conductor is not null then
    select o.nomina_op into new.nomina from public.catalogo_operadores o
     where upper(trim(o.nombre_op)) = upper(trim(new.nombre_conductor)) limit 1;
  end if;
  return new;
end $$;
drop trigger if exists lipu_completar_evento on public.base_eventos;
create trigger lipu_completar_evento before insert on public.base_eventos for each row execute function public.lipu_completar_evento();

create index if not exists catalogo_eventos_tipo_idx on public.catalogo_eventos (tipo_evento);
create index if not exists base_viajes_num_economico_idx on public.base_viajes (num_economico);
create index if not exists base_eventos_num_economico_idx on public.base_eventos (num_economico);

select (select count(*) from public.resumen_viajes_dia) resumen_viajes, (select count(*) from public.resumen_eventos_dia) resumen_eventos,
       (select count(*) from public.base_viajes) base_viajes, (select count(*) from public.base_eventos) base_eventos,
       pg_size_pretty(pg_database_size(current_database())) tam_bd;
