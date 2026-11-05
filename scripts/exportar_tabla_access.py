"""
Exporta tablas de CARGAR BASES PRINCIPALES.accdb a CSV comprimido (.csv.gz) en OneDrive, sin modificar el Access.

Uso (doble clic): exporta las tres tablas base de Supabase
    - TABLA DRIVES HOY        completa (solo trae lo del día)
    - TABLA DE VIAJES TL      últimos 62 días
    - TABLA DE EVENTOS TL     últimos 62 días
Desde cmd, una sola tabla:
    py exportar_tabla_access.py "NOMBRE DE LA TABLA" [días]
Luego cárgalas en el portal → Cargas de datos.
"""
import gzip
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pyodbc

BASE = Path(r"C:\Users\carde\OneDrive - Traxión\USER CARDEJC\01 Principal")
ACCESS = BASE / r"00 DESARROLLOS\CARGAR BASES PRINCIPALES.accdb"
SALIDA = BASE / r"00 DESARROLLOS\DATOS TABLEROS\access"
TABLAS = [("TABLA DRIVES HOY", None), ("TABLA DE VIAJES TL", 62), ("TABLA DE EVENTOS TL", 62)]


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


def exportar(cur, tablas, nombre, dias):
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
    tabla = next((x for x in tablas if x == nombre), None) or next((x for x in tablas if norm(x) == norm(nombre)), None)
    if not tabla:
        print(f"  ✗ No encontré «{nombre}». Tablas: {', '.join(tablas)}")
        return
    tipos = {c.column_name: c.type_name for c in cur.columns(table=tabla)}
    sql, filtro = f"SELECT * FROM [{tabla}]", ""
    if dias:
        col = columna_fecha(tipos)
        if col:
            desde = date.today() - timedelta(days=dias)
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
    pedido = [(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)] if len(sys.argv) > 1 else TABLAS
    print(f"Abriendo {ACCESS.name}…")
    con = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + str(ACCESS))
    cur = con.cursor()
    tablas = [r.table_name for r in cur.tables(tableType="TABLE")]
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, dias in pedido:
        exportar(cur, tablas, nombre, dias)
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
