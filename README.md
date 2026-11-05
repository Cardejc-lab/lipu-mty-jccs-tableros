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

## Actualizar los datos de cruces

1. Actualiza `BASE DE CRUCES FERROVIARIOS.accdb`, la hoja PLANTILLA y, si hace falta, `Ubicacion de los Puntos de Cruce.xlsx`.
2. Ejecuta `py exportar_cruces.py`. Deja `cruces_lipu_mty.csv.gz` y `ubicaciones.json` en `OneDrive\…\00 DESARROLLOS\DATOS TABLEROS\cruces`.
3. Abre el tablero con tu cuenta de administrador → **Cargar archivo** → elige los dos archivos → **Publicar para todos**.

Requisitos del script (una sola vez): `py -m pip install pandas pyodbc openpyxl` y el controlador *Microsoft Access Database Engine* de 64 bits.

## Usuarios

- Alta: Supabase → proyecto **prueba_desarrollos** → Authentication → Users → **Add user → Send invitation**. La persona recibe un correo y crea su contraseña en el portal.
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
