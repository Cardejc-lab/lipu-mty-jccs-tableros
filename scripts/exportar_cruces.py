"""
Exporta los datos del tablero de Cruces Ferroviarios (Lipu Monterrey).

Lee:
  - BASE DE CRUCES FERROVIARIOS.accdb   (tabla CRUCES DE FERROCARRIL)
  - TABLAS PARA REPORTES.xlsx           (hoja PLANTILLA)
  - Ubicacion de los Puntos de Cruce.xlsx
Escribe en OneDrive (00 DESARROLLOS\\DATOS TABLEROS\\cruces):
  - cruces_lipu_mty.csv.gz   (eventos limpios)
  - ubicaciones.json         (coordenadas de cada cruce)
Los datos NUNCA se suben a GitHub. Para publicarlos: abre el tablero, inicia sesión como administrador,
pulsa «Cargar archivo», elige los dos archivos y luego «Publicar para todos».

Uso (Windows):
    py exportar_cruces.py

Requisitos (una sola vez):
    py -m pip install pandas pyodbc openpyxl
    y el controlador "Microsoft Access Database Engine" de la misma arquitectura que Python (64 bits).
"""
import gzip
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyodbc

# ---------------- Rutas (ajusta si cambian) ----------------
BASE = Path(r"C:\Users\carde\OneDrive - Traxión\USER CARDEJC\01 Principal")
ACCESS = BASE / r"00 DESARROLLOS\BASE DE CRUCES FERROVIARIOS.accdb"
TABLA = "CRUCES DE FERROCARRIL"
PLANTILLA = BASE / r"02 ARCHIVOS PARA REPORTE\TABLAS PARA REPORTES.xlsx"
UBICACIONES = BASE / r"CRUCES DE FERROCARRIL\Ubicacion de los Puntos de Cruce.xlsx"
SALIDA = BASE / r"00 DESARROLLOS\DATOS TABLEROS\cruces"

# Nombres de cruce escritos distinto entre el Access y el Excel de ubicaciones
ALIAS = {"CAM. A SAN LUIS": "CAM. SAN LUIS"}


def key(s):
    s = re.sub(r"^\s*vias\s+", "", str(s), flags=re.I)
    return re.sub(r"\s+", " ", s).strip().upper()


def proper(s):
    s = "" if s is None or (isinstance(s, float) and pd.isna(s)) else str(s).strip()
    return " ".join(w.capitalize() for w in s.split())


def a_segundos(v):
    """La duración viene como hora (1899-12-30 hh:mm:ss) o como texto hh:mm:ss."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, datetime):
        return (v - datetime(1899, 12, 30)).total_seconds()
    if hasattr(v, "hour"):
        return v.hour * 3600 + v.minute * 60 + v.second
    s = str(v).strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        t = pd.to_datetime(s, errors="coerce")
        return None if pd.isna(t) else (t - pd.Timestamp("1899-12-30")).total_seconds()
    m = re.search(r"(\d+):(\d{2}):(\d{2})", s)
    return int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) if m else None


def leer_access():
    con = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + str(ACCESS))
    d = pd.read_sql(f"SELECT * FROM [{TABLA}]", con)
    con.close()
    return d


def main():
    print(f"Leyendo {ACCESS.name}…")
    d = leer_access()
    st = {"filas_access": len(d)}
    d = d[d["Nombre de capa / categoría"].astype(str).str.lower() == "vias"]
    d = d[d["Hora de entrada"].notna()]
    d = d.sort_values("Actualizacion").drop_duplicates(["Número de vehículo", "Hora de entrada", "Nombre de geometría"], keep="last")
    st["sin_duplicados"] = len(d)

    dur = d["Duración en la ubicación"].map(a_segundos)
    alt = (pd.to_datetime(d["Hora de salida"], errors="coerce") - pd.to_datetime(d["Hora de entrada"])).dt.total_seconds().round()
    d["dur"] = pd.to_numeric(dur, errors="coerce").fillna(alt).round()
    d = d[d["dur"].notna() & (d["dur"] >= 0)]

    print(f"Leyendo plantilla de {PLANTILLA.name}…")
    p = pd.read_excel(PLANTILLA, "PLANTILLA")
    p = p[pd.to_numeric(p["NOMINA"], errors="coerce").notna()].copy()
    p["n"] = pd.to_numeric(p["NOMINA"]).astype("int64").astype(str)
    p = p.drop_duplicates("n").set_index("n")[["COORDINADOR ", "JEFE DE COORDINADOR", "GERENTE COORD"]]

    d["n"] = pd.to_numeric(d["ID de empleado"], errors="coerce").astype("Int64").astype(str).replace("<NA>", "")
    j = d.join(p, on="n")
    km = pd.to_numeric(j["Distancia conducida en la ubicación (km)"], errors="coerce")
    km = km.where((km >= 0) & (km <= 5))

    out = pd.DataFrame({
        "fecha_hora": pd.to_datetime(j["Hora de entrada"]).dt.strftime("%Y-%m-%d %H:%M:%S"),
        "dur_seg": j["dur"].astype(int),
        "unidad": j["Número de vehículo"].astype(str),
        "nomina": j["n"],
        "operador": j["Nombre del conductor"].map(proper),
        "planta": j["Grupo de vehículos"].map(proper),
        "cruce": j["Nombre de geometría"].map(lambda s: proper(key(s))),
        "km": km.round(2),
        "coordinador": j["COORDINADOR "].map(proper),
        "jefe": j["JEFE DE COORDINADOR"].map(proper),
        "gerente": j["GERENTE COORD"].map(proper),
    }).sort_values("fecha_hora")
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].fillna("").astype(str).str.replace(",", ";").str.replace("\n", " ")

    SALIDA.mkdir(parents=True, exist_ok=True)
    with gzip.open(SALIDA / "cruces_lipu_mty.csv.gz", "wt", encoding="utf-8", newline="") as f:
        out.to_csv(f, index=False, lineterminator="\n")

    print(f"Leyendo ubicaciones de {UBICACIONES.name}…")
    g = pd.read_excel(UBICACIONES)
    geo = {}
    for _, r in g.iterrows():
        nums = re.findall(r"-?\d+(?:\.\d+)?", str(r["Coordenadas"]))
        if len(nums) >= 2 and 24 < float(nums[0]) < 27 and -102 < float(nums[1]) < -98:
            geo[key(r["Nombre de geometría"])] = [round(float(nums[0]), 6), round(float(nums[1]), 6)]
    for a, b in ALIAS.items():
        if b in geo:
            geo[a] = geo[b]
    (SALIDA / "ubicaciones.json").write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")

    cr = set(out["cruce"].map(key))
    sin = sorted(cr - set(geo))
    print(f"Listo: {len(out):,} eventos del {out.fecha_hora.min()[:10]} al {out.fecha_hora.max()[:10]} "
          f"(Access: {st['filas_access']:,} filas). Cruces con ubicación: {len(cr & set(geo))} de {len(cr)}.")
    if sin:
        print("Sin coordenadas:", ", ".join(sin))
    print(f"Archivos en: {SALIDA}")
    print("Para publicarlos: abre el tablero, «Cargar archivo» → elige los dos archivos → «Publicar para todos».")


if __name__ == "__main__":
    try:
        main()
    except pyodbc.Error as e:
        sys.exit(f"No se pudo abrir el Access. ¿Está instalado el controlador de Access de 64 bits y el archivo cerrado?\n{e}")
