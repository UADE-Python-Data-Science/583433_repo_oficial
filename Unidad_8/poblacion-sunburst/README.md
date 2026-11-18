# Población mundial · Zoomable Sunburst (D3 + World Bank)

Sunburst interactivo con la población total por **Mundo → Región → País** para el
último año disponible en los World Development Indicators del Banco Mundial.

## Estructura

```
├── index.html             # Gráfico D3 v7 (sin build, se carga D3 desde jsDelivr)
├── data/poblacion.json    # Árbol jerárquico generado por el script
├── scripts/build_data.py  # API World Bank -> JSON
└── requirements.txt
```

## 1. Generar los datos

```bash
pip install -r requirements.txt
python scripts/build_data.py            # nombres en español
python scripts/build_data.py --lang en  # nombres en inglés
```

El script:
1. Descarga `WB_WDI_SP_POP_TOTL` de la **Data360 API** (paginado de a 1000).
2. Descarga la clasificación de países de la **API v2** (`/v2/es/country`) y
   descarta los agregados (región `NA`) para no contar dos veces.
3. Toma el último año disponible, arma el árbol y lo guarda en `data/poblacion.json`.
4. Compara la suma de países contra el agregado `WLD` como control.

## 2. Probar localmente

```bash
python -m http.server
# abrir http://localhost:8000
```

> Abrir `index.html` con doble clic (`file://`) no funciona: el navegador bloquea
> la lectura del JSON.

## 3. Publicar en GitHub Pages

```bash
git init
git add .
git commit -m "Sunburst de población mundial"
git branch -M main
git remote add origin https://github.com/<usuario>/poblacion-sunburst.git
git push -u origin main
```

En GitHub: **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`**.
El sitio queda en `https://<usuario>.github.io/poblacion-sunburst/`.

## Actualizar los datos

```bash
python scripts/build_data.py
git add data/poblacion.json
git commit -m "Actualiza datos de población"
git push
```

Fuente: Banco Mundial, World Development Indicators (SP.POP.TOTL).
Gráfico basado en [Zoomable Sunburst](https://observablehq.com/@d3/zoomable-sunburst) de Mike Bostock (ISC).
