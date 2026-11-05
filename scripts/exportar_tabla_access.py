"""
Exporta una tabla de un Access a CSV comprimido (.csv.gz) en OneDrive, sin modificar el Access.

Uso (doble clic o desde cmd):
    py exportar_tabla_access.py
Por defecto exporta «TABLA DRIVES HOY» de CARGAR BASES PRINCIPALES.accdb.
Para otra tabla:
    py exportar_tabla_access.py "NOMBRE DE LA TABLA"
"""
import gzip
import re
import sys
from pathlib import Path

import pandas as pd
import pyodbc

BASE = Path(r"C:\Users\carde\OneDrive - Traxión\USER CARDEJC\01 Principal")
ACCESS = BASE / r"00 DESARROLLOS\CARGAR BASES PRINCIPALES.accdb"
TABLA = sys.argv[1] if len(sys.argv) > 1 else "TABLA DRIVES HOY"
SALIDA = BASE / r"00 DESARROLLOS\DATOS TABLEROS\access"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def main():
    print(f"Abriendo {ACCESS.name}…")
    con = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + str(ACCESS))
    cur = con.cursor()
    tablas = [r.table_name for r in cur.tables(tableType="TABLE")]
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
    tabla = next((x for x in tablas if x == TABLA), None) or next((x for x in tablas if norm(x) == norm(TABLA)), None)
    if not tabla:
        raise RuntimeError(f"No encontré «{TABLA}». Tablas en el Access: {', '.join(tablas)}")

    tipos = {c.column_name: c.type_name for c in cur.columns(table=tabla)}
    print(f"Leyendo «{tabla}» ({len(tipos)} columnas)…")
    cur.execute(f"SELECT * FROM [{tabla}]")
    cols = [c[0] for c in cur.description]
    d = pd.DataFrame.from_records(cur.fetchall(), columns=cols)
    con.close()

    SALIDA.mkdir(parents=True, exist_ok=True)
    archivo = SALIDA / f"{slug(tabla)}.csv.gz"
    with gzip.open(archivo, "wt", encoding="utf-8", newline="") as f:
        d.to_csv(f, index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S")
    (SALIDA / f"{slug(tabla)}_columnas.txt").write_text(
        "\n".join(f"{c}\t{tipos.get(c, '')}" for c in cols), encoding="utf-8")

    print(f"\nListo: {len(d):,} filas · {len(cols)} columnas")
    print(f"Archivo: {archivo}  ({archivo.stat().st_size / 1e6:,.1f} MB)")
    print("\nColumnas:")
    for c in cols:
        print(f"  - {c}  [{tipos.get(c, '')}]")
    print("\nOtras tablas del Access:", ", ".join(t for t in tablas if t != tabla))


if __name__ == "__main__":
    try:
        main()
    except pyodbc.Error as e:
        print(f"No se pudo leer el Access. ¿Está abierto en modo exclusivo o falta el controlador de 64 bits?\n{e}")
    except Exception as e:
        print(f"Error: {e}")
    input("\nPresiona Enter para cerrar…")
