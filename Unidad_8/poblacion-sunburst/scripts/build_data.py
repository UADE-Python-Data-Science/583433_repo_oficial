"""
build_data.py
-------------
Descarga la población total de la API del Banco Mundial y genera un JSON
jerárquico (Mundo -> Región -> País) para el gráfico Zoomable Sunburst de D3.

Fuentes:
  1) Data360 API  -> valores de población (indicador WB_WDI_SP_POP_TOTL)
  2) API v2       -> clasificación de cada país (región) y nombres en español

Uso (desde la raíz del repo):
    python scripts/build_data.py
    python scripts/build_data.py --lang en --out data/poblacion.json

Salida: data/poblacion.json
"""

import argparse
import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

DATA360_URL = "https://data360api.worldbank.org/data360/data"
COUNTRY_URL = "https://api.worldbank.org/v2/{lang}/country"
INDICATOR = "WB_WDI_SP_POP_TOTL"


# ---------------------------------------------------------------------------
# 1. Helpers HTTP
# ---------------------------------------------------------------------------
def get_json(url, params=None, retries=3):
    """GET con reintentos simples. Devuelve el JSON de la respuesta."""
    for intento in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if intento == retries:
                raise
            print(f"  Error ({e}). Reintento {intento}/{retries - 1}...")
            time.sleep(2 * intento)


# ---------------------------------------------------------------------------
# 2. Población (Data360) - misma lógica de paginación que el notebook U6_NB4
# ---------------------------------------------------------------------------
def fetch_population():
    params = {
        "DATABASE_ID": "WB_WDI",
        "INDICATOR": INDICATOR,
        "skip": 0,
        "limit": 1000,
    }
    registros = []
    total = None

    while total is None or len(registros) < total:
        params["skip"] = len(registros)
        resp = get_json(DATA360_URL, params)
        total = resp.get("count", 0)
        pagina = resp.get("value", [])
        if not pagina:  # corte de seguridad
            break
        registros.extend(pagina)
        print(f"  Población: {len(registros)} de {total} registros")

    df = pd.DataFrame(registros)

    # Nos quedamos con el total (sin desagregar por sexo, edad ni urbanización)
    for col in ["SEX", "AGE", "URBANISATION"]:
        if col in df.columns:
            df = df[df[col].fillna("_T") == "_T"]

    df = df[["REF_AREA", "TIME_PERIOD", "OBS_VALUE"]].copy()
    df["TIME_PERIOD"] = pd.to_numeric(df["TIME_PERIOD"], errors="coerce")
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df = df.dropna().drop_duplicates(["REF_AREA", "TIME_PERIOD"])
    df["TIME_PERIOD"] = df["TIME_PERIOD"].astype(int)
    return df


# ---------------------------------------------------------------------------
# 3. Clasificación de países (API v2)
# ---------------------------------------------------------------------------
def fetch_countries(lang="es"):
    """
    Devuelve un DataFrame con: iso3, pais, region_id, region.
    La API v2 marca a los agregados (WLD, LCN, HIC, EUU...) con
    region.id == "NA" ("Aggregates"); esos se descartan para no contar dos veces.
    """
    resp = get_json(COUNTRY_URL.format(lang=lang), {"format": "json", "per_page": 500})
    meta, filas = resp[0], resp[1]
    if meta.get("pages", 1) > 1:
        raise RuntimeError("La lista de países vino paginada: subir per_page.")

    paises = [
        {
            "iso3": f["id"],
            "pais": f["name"].strip(),
            "region_id": f["region"]["id"],
            "region": f["region"]["value"].strip(),
        }
        for f in filas
        if f["region"]["id"] != "NA"  # fuera los agregados
    ]
    df = pd.DataFrame(paises)
    print(f"  Clasificación: {len(df)} países en {df['region_id'].nunique()} regiones")
    return df


# ---------------------------------------------------------------------------
# 4. Armado del árbol Mundo -> Región -> País
# ---------------------------------------------------------------------------
def build_tree(pop, paises):
    # Unimos población con clasificación: solo quedan países reales
    df = pop.merge(paises, left_on="REF_AREA", right_on="iso3", how="inner")

    # Último año disponible entre los países
    anio = int(df["TIME_PERIOD"].max())
    df_anio = df[df["TIME_PERIOD"] == anio]

    faltantes = sorted(set(paises["pais"]) - set(df_anio["pais"]))
    if faltantes:
        print(f"  Aviso: {len(faltantes)} países sin dato para {anio} "
              f"(quedan fuera): {', '.join(faltantes)}")

    regiones = []
    for (region_id, region), grupo in df_anio.groupby(["region_id", "region"]):
        hijos = [
            {"name": r.pais, "code": r.iso3, "value": int(r.OBS_VALUE)}
            for r in grupo.sort_values("OBS_VALUE", ascending=False).itertuples()
        ]
        regiones.append({"name": region, "code": region_id, "children": hijos})

    # Control: la suma de países debería coincidir (aprox.) con el agregado WLD
    total = int(df_anio["OBS_VALUE"].sum())
    wld = pop[(pop["REF_AREA"] == "WLD") & (pop["TIME_PERIOD"] == anio)]["OBS_VALUE"]
    if not wld.empty:
        dif = (total - wld.iloc[0]) / wld.iloc[0] * 100
        print(f"  Control: suma de países = {total:,} | WLD = {int(wld.iloc[0]):,} "
              f"| diferencia = {dif:+.2f}%")

    arbol = {
        "name": "Mundo",
        "year": anio,
        "source": "World Bank - WDI, SP.POP.TOTL (Data360 API)",
        "generated": date.today().isoformat(),
        "children": sorted(regiones, key=lambda r: r["code"]),
    }
    return arbol, len(df_anio)


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/poblacion.json", help="archivo de salida")
    parser.add_argument("--lang", default="es", help="idioma de los nombres (es, en, fr...)")
    args = parser.parse_args()

    print("1/3 Descargando población (Data360)...")
    pop = fetch_population()

    print("2/3 Descargando clasificación de países (API v2)...")
    paises = fetch_countries(args.lang)

    print("3/3 Armando jerarquía Mundo -> Región -> País...")
    arbol, n = build_tree(pop, paises)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(arbol, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nListo: {out} | año {arbol['year']} | "
          f"{len(arbol['children'])} regiones | {n} países")


if __name__ == "__main__":
    main()
