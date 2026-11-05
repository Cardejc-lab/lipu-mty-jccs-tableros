"""
Exporta tablas de CARGAR BASES PRINCIPALES.accdb a CSV comprimido (.csv.gz) en OneDrive, sin modificar el Access.

Uso (doble clic): exporta las tres tablas base de Supabase
    - TABLA DRIVES HOY        completa (solo trae lo del día)
    - TABLA DE VIAJES TL      solo lo nuevo: desde el último día cargado en Supabase menos 2 días de repaso
    - TABLA DE EVENTOS TL     igual que viajes
  Si no hay conexión con Supabase, exporta los últimos 62 días (carga completa de la ventana).
  Para forzar la carga completa de 62 días:  py exportar_tabla_access.py completa
Desde cmd, una sola tabla:
    py exportar_tabla_access.py "NOMBRE DE LA TABLA" [días]
Luego cárgalas en el portal → Cargas de datos.
"""
import gzip
import json
import urllib.request
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pyodbc

BASE = Path(r"C:\Users\carde\OneDrive - Traxión\USER CARDEJC\01 Principal")
ACCESS = BASE / r"00 DESARROLLOS\CARGAR BASES PRINCIPALES.accdb"
SALIDA = BASE / r"00 DESARROLLOS\DATOS TABLEROS\access"
TABLAS = [("TABLA DRIVES HOY", None), ("TABLA DE VIAJES TL", 62), ("TABLA DE EVENTOS TL", 62)]
VENTANA_DIAS = 62
REPASO_DIAS = 2   # días ya cargados que se vuelven a exportar por si llegaron registros tardíos
SUPABASE = "https://xbzovcjjxrupuygarnbk.supabase.co"
LLAVE_PUBLICA = "sb_publishable_l_KnKdVzUVxbs6K7UV1uhg_y35uRU7i"   # pública: la función solo devuelve fechas


def ultimos_dias():
    """{tabla: último día cargado en Supabase} o {} si no hay conexión."""
    try:
        req = urllib.request.Request(f"{SUPABASE}/rest/v1/rpc/lipu_ultimo_dia", data=b"{}", method="POST",
                                     headers={"apikey": LLAVE_PUBLICA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return {x["tabla"]: datetime.strptime(x["ultimo_dia"], "%Y-%m-%d").date()
                    for x in json.load(r) if x.get("ultimo_dia")}
    except Exception as e:
        print(f"  (No se pudo consultar Supabase: {e}. Se exportan {VENTANA_DIAS} días.)")
        return {}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def columna_fecha(cols):
    """Primera columna de fecha/hora cuyo nombre sugiere inicio; si no, la primera de fecha."""
    fechas = [c for c, t in cols.items() if "DATE" in t.upper() or "TIME" in t.upper()]
    for pista in ("inicio", "hora de inicio", "fecha"):
        for c in fechas:
            if pista in c.lower() and "manejo" not in c.lower() and "ralent" not in c.lower():
                return c
    return fechas[0] if fechas else None


def exportar(cur, tablas, nombre, dias, desde=None):
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
    tabla = next((x for x in tablas if x == nombre), None) or next((x for x in tablas if norm(x) == norm(nombre)), None)
    if not tabla:
        print(f"  ✗ No encontré «{nombre}». Tablas: {', '.join(tablas)}")
        return
    tipos = {c.column_name: c.type_name for c in cur.columns(table=tabla)}
    sql, filtro = f"SELECT * FROM [{tabla}]", ""
    if dias or desde:
        col = columna_fecha(tipos)
        if col:
            desde = desde or date.today() - timedelta(days=dias)
            sql += f" WHERE [{col}] >= #{desde:%m/%d/%Y}#"
            filtro = f" (desde {desde:%d/%m/%Y} por «{col}»)"
    print(f"Leyendo «{tabla}»{filtro}…")
    cur.execute(sql)
    cols = [c[0] for c in cur.description]
    d = pd.DataFrame.from_records(cur.fetchall(), columns=cols)
    archivo = SALIDA / f"{slug(tabla)}.csv.gz"
    with gzip.open(archivo, "wt", encoding="utf-8", newline="") as f:
        d.to_csv(f, index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S")
    (SALIDA / f"{slug(tabla)}_columnas.txt").write_text("\n".join(f"{c}\t{tipos.get(c, '')}" for c in cols), encoding="utf-8")
    print(f"  ✓ {len(d):,} filas · {len(cols)} columnas · {archivo.name} ({archivo.stat().st_size / 1e6:,.1f} MB)")


def main():
    completa = len(sys.argv) > 1 and sys.argv[1].lower() == "completa"
    pedido = [(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)] if len(sys.argv) > 1 and not completa else TABLAS
    inicio = {}
    if not completa and pedido is TABLAS:
        print("Consultando en Supabase el último día cargado…")
        tope = date.today() - timedelta(days=VENTANA_DIAS)
        for tabla, ultimo in ultimos_dias().items():
            inicio[tabla] = max(ultimo - timedelta(days=REPASO_DIAS), tope)
            print(f"  {tabla}: último día en Supabase {ultimo:%d/%m/%Y} → se exporta desde {inicio[tabla]:%d/%m/%Y}")
    print(f"Abriendo {ACCESS.name}…")
    con = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + str(ACCESS))
    cur = con.cursor()
    tablas = [r.table_name for r in cur.tables(tableType="TABLE")]
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, dias in pedido:
        exportar(cur, tablas, nombre, dias, inicio.get(nombre))
    con.close()
    print(f"\nArchivos en: {SALIDA}")
    print("Siguiente paso: portal → Cargas de datos → «Cargar archivo» en cada tabla.")


if __name__ == "__main__":
    try:
        main()
    except pyodbc.Error as e:
        print(f"No se pudo leer el Access. ¿Está abierto o falta el controlador de 64 bits?\n{e}")
    except Exception as e:
        print(f"Error: {e}")
    input("\nPresiona Enter para cerrar…")
