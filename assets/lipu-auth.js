/* Sesión compartida de los tableros Lipu Monterrey (Supabase Auth + Storage privado).
   La llave "publishable" es pública por diseño: el acceso real lo controlan las reglas del proyecto
   (solo usuarios invitados inician sesión; solo ellos leen el almacén privado «datos»). */
(function () {
  "use strict";
  const CFG = {
    url: "https://xbzovcjjxrupuygarnbk.supabase.co",
    key: "sb_publishable_l_KnKdVzUVxbs6K7UV1uhg_y35uRU7i",
    bucket: "datos",
    admins: ["cardejc@live.com"],          /* quién puede publicar datos nuevos (también lo valida Supabase) */
    portal: new URL("../", document.currentScript.src).href   /* raíz del sitio */
  };
  let client = null;
  function sb() {
    if (client) return client;
    if (!window.supabase || !window.supabase.createClient) throw { code: "nolib", msg: "No cargó la librería de inicio de sesión. Revisa tu conexión y recarga." };
    client = window.supabase.createClient(CFG.url, CFG.key, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, storageKey: "lipu-mty-auth" } });
    return client;
  }
  async function session() { try { const { data } = await sb().auth.getSession(); return data.session || null; } catch (e) { return null; } }
  async function user() { const s = await session(); return s ? s.user : null; }
  async function isAdmin() { const u = await user(); return !!u && CFG.admins.includes(String(u.email || "").toLowerCase()); }
  /* Descarga un archivo del almacén privado; requiere sesión */
  async function download(path) {
    const s = await session();
    if (!s) throw { code: "nosession", msg: "Inicia sesión en el portal para ver los datos." };
    const { data, error } = await sb().storage.from(CFG.bucket).download(path);
    if (error) throw { code: "storage", msg: /not.?found|404/i.test(error.message || "") ? `Aún no hay datos publicados (${path}).` : `No se pudieron descargar los datos: ${error.message}` };
    return data; /* Blob */
  }
  /* Sube o reemplaza un archivo (solo administradores) */
  async function upload(path, blob, contentType) {
    const { error } = await sb().storage.from(CFG.bucket).upload(path, blob, { upsert: true, contentType: contentType || "application/octet-stream", cacheControl: "60" });
    if (error) throw { code: "upload", msg: `No se pudo publicar ${path}: ${error.message}` };
  }
  async function info(path) {
    const dir = path.split("/").slice(0, -1).join("/"), name = path.split("/").pop();
    const { data } = await sb().storage.from(CFG.bucket).list(dir, { search: name });
    return (data || []).find(f => f.name === name) || null;
  }
  window.LIPU = { CFG, sb, session, user, isAdmin, download, upload, info };
})();
