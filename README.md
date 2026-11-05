# Portal de tableros · Lipu Monterrey

Portal con los tableros operativos de Lipu Monterrey, publicado gratis en **GitHub Pages**.
Este repositorio contiene **solo código**. Los datos viven en un almacén **privado** de Supabase y solo los leen usuarios invitados que inician sesión.

```
Access / Excel (OneDrive) ──► scripts/exportar_cruces.py ──► archivos en OneDrive
                                                             │
                     Tablero (admin) «Publicar para todos» ◄─┘
                                                             │
                           Supabase Storage privado «datos» ─┴─► Tablero con sesión iniciada
```

## Contenido

| Ruta | Qué es |
|---|---|
| `index.html` | Portal: inicio de sesión y menú de tableros |
| `assets/lipu-auth.js` | Sesión compartida (Supabase Auth) y acceso al almacén privado |
| `cruces/` | Tablero de cruces ferroviarios (ejecutivo, no altos, semanal con días comparables, mapa, por revisar, detalle) |
| `cruces/basemap.json` | Base del mapa: municipios y AGEB urbanas (INEGI), carreteras, vías del tren y ríos (Natural Earth). Datos públicos. |
| `scripts/exportar_cruces.py` | Genera los datos del tablero desde el Access y los Excel, en OneDrive |
| `scripts/exportar_tabla_access.py` | Exporta cualquier tabla del Access a `.csv.gz` (por defecto TABLA DRIVES HOY) |
| `cargas/` | Página de administración: carga a Supabase las tablas exportadas del Access |

## Actualizar los datos de cruces

1. Actualiza `BASE DE CRUCES FERROVIARIOS.accdb`, la hoja PLANTILLA y, si hace falta, `Ubicacion de los Puntos de Cruce.xlsx`.
2. Ejecuta `py exportar_cruces.py`. Deja `cruces_lipu_mty.csv.gz` y `ubicaciones.json` en `OneDrive\…\00 DESARROLLOS\DATOS TABLEROS\cruces`.
3. Abre el tablero con tu cuenta de administrador → **Cargar archivo** → elige los dos archivos → **Publicar para todos**.

Requisitos del script (una sola vez): `py -m pip install pandas pyodbc openpyxl` y el controlador *Microsoft Access Database Engine* de 64 bits.

## Tablas en Supabase (proyecto prueba_desarrollos)

| Tabla | Origen | Regla de carga |
|---|---|---|
| `base_viajes_hoy` | TABLA DRIVES HOY (CARGAR BASES PRINCIPALES.accdb) | Reemplazo completo en cada carga (solo lo que va del día) |
| `base_viajes`, `base_eventos` | TABLA DE VIAJES TL / TABLA DE EVENTOS TL | Ventana de 62 días a detalle (página Cargas). Lo anterior pasa a `resumen_viajes_dia` / `resumen_eventos_dia`. `num_economico` = «Núm Económico», `id_viaje` = «Núm Eco» |
| `catalogo_operadores`, `catalogo_vehiculos`, `catalogo_eventos` | Catálogos | Pendiente de actualizar |

Para actualizar (carga diferencial): `py exportar_tabla_access.py` consulta en Supabase el último día cargado y exporta solo desde ese día menos 2 de repaso (DRIVES HOY siempre completa; `completa` como argumento fuerza los 62 días) → portal → **Cargas de datos** → en cada tabla «Cargar archivo» → «Confirmar carga». Viajes y eventos reemplazan los días del archivo y cierran la ventana de 62 días.

**Llaves comunes:** `num_economico` = número de unidad («Núm Económico» del Access) · `nomina` / `id_colaborador` = nómina del operador · planta = grupo de vehículos.

## Usuarios

- Alta: Supabase → proyecto **prueba_desarrollos** → Authentication → Users → **Add user → Create new user**: correo, contraseña temporal y **Auto Confirm User** activado. Entrega la contraseña temporal en persona; la persona la cambia en el portal con **Cambiar contraseña**.
- El correo de Supabase sin SMTP propio solo envía a miembros del proyecto (2 correos por hora), por eso las invitaciones y «¿Olvidaste tu contraseña?» no llegan a otros usuarios. Para habilitarlas, configura un SMTP gratuito (por ejemplo Brevo) en Authentication → Emails → SMTP Settings.
- Baja: Authentication → Users → menú del usuario → **Delete user** (deja de entrar de inmediato).
- Los registros abiertos están desactivados: nadie entra sin invitación.
- Administradores (pueden publicar datos): lista `admins` en `assets/lipu-auth.js` y reglas *Admin …* del almacén `datos` en Supabase. Hay que cambiar ambas.

## Reglas de clasificación (cruces)

| Segundos dentro de la geocerca | Evento |
|---|---|
| menos de 5 | No hizo alto |
| 5 a 10 | Alto parcial |
| 11 a 120 | Hizo alto |
| más de 120 | Posible paso del tren (cuenta como cumplimiento) |

Los umbrales y metas están en `CONFIG` al inicio de `cruces/index.html`.

## Agregar un tablero nuevo

1. Crea una carpeta (por ejemplo `alarmas/`) con su `index.html` y carga `../assets/lipu-auth.js`.
2. Sube sus datos al almacén con la misma función de «Publicar para todos» (ruta `alarmas/...`).
3. Agrega su botón en `index.html` con `data-trx-modal="alarmas/"`.

> Nunca subas archivos de datos (`.csv`, `.accdb`, `.xlsx`) a este repositorio: es público.
