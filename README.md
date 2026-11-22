# Portal de tableros · Lipu Monterrey

Portal con los tableros operativos de Lipu Monterrey, publicado gratis en **GitHub Pages**.
Este repositorio contiene **solo código**. Los datos viven en un almacén **privado** de Supabase y solo los leen usuarios invitados que inician sesión.

## Contenido

| Ruta | Qué es |
|---|---|
| `index.html` | Portal: inicio de sesión y menú de tableros |
| `assets/tema-lipu/` | Tema verde Lipu (CSS), logos (`logo-lipu.png`, `logo-derecho.png`, `marca-agua.png`) y `plantilla.html` para tableros nuevos |
| `assets/lipu-auth.js` | Sesión compartida (Supabase Auth) y acceso al almacén privado |

El tablero de **Cruces ferroviarios** y su script `exportar_cruces.py` se retiraron el 22-nov-2026: Cruces ahora se calcula desde el Access con el ETL local del proyecto TABLEROS LIPU (`desarrollos\cruces.py`), publica snapshots `snap_cru_*` en Supabase y su tablero vive como artefacto en Claude, pendiente de migrar a este portal.

## Datos de viajes, eventos y demás desarrollos

Ya no se cargan desde este portal. Los desarrollos operativos (Uso DMAS, Descansos, Score de seguridad, Ralentí, etc.) se calculan desde los Access con el ETL local del proyecto TABLEROS LIPU y publican snapshots `snap_*` en Supabase. La página «Cargas» se retiró el 21-nov-2026.

## Usuarios

- Alta: Supabase → proyecto **prueba_desarrollos** → Authentication → Users → **Add user → Create new user**: correo, contraseña temporal y **Auto Confirm User** activado. Entrega la contraseña temporal en persona; la persona la cambia en el portal con **Cambiar contraseña**.
- El correo de Supabase sin SMTP propio solo envía a miembros del proyecto (2 correos por hora), por eso las invitaciones y «¿Olvidaste tu contraseña?» no llegan a otros usuarios. Para habilitarlas, configura un SMTP gratuito (por ejemplo Brevo) en Authentication → Emails → SMTP Settings.
- Baja: Authentication → Users → menú del usuario → **Delete user** (deja de entrar de inmediato).
- Los registros abiertos están desactivados: nadie entra sin invitación.
- Administradores (pueden publicar datos): lista `admins` en `assets/lipu-auth.js` y reglas *Admin …* del almacén `datos` en Supabase. Hay que cambiar ambas.

## Agregar un tablero nuevo

1. Crea una carpeta (por ejemplo `alarmas/`) con su `index.html` y carga `../assets/lipu-auth.js`.
2. Sube sus datos al almacén con la misma función de «Publicar para todos» (ruta `alarmas/...`).
3. Agrega su botón en `index.html` con `data-trx-modal="alarmas/"`.

> Nunca subas archivos de datos (`.csv`, `.accdb`, `.xlsx`) a este repositorio: es público.
