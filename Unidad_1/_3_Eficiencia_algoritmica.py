from timeit import timeit
import pandas as pd

tacos = [
    {"id": "SDT-001", "nombre": "Tacos El Gordo", "score": 4.6, "lat": 32.6305, "lon": -117.0601},
    {"id": "SDT-002", "nombre": "The Taco Stand", "score": 4.7, "lat": 32.8427, "lon": -117.2731},
    {"id": "SDT-003", "nombre": "Las Cuatro Milpas", "score": 4.8, "lat": 32.7003, "lon": -117.1431},
    {"id": "SDT-004", "nombre": "Lucha Libre Taco Shop", "score": 4.3, "lat": 32.7441, "lon": -117.1724},
]

# metodo 1
def trasponer_1(tacos):
    tacos_por_columna = {
    "nombre": [],
    "score": []
    }

    for taco in tacos:
        tacos_por_columna["nombre"].append(taco["nombre"]) #nombre
        tacos_por_columna["score"].append(taco["score"]) #score
    return tacos_por_columna

# metodo 2
def trasponer_2(tacos):
    tacos_por_columna = {}
    nombre = []
    score = []
    for t in tacos:
        nombre.append(t["nombre"])
        score.append(t["score"])
    tacos_por_columna["nombre"] = nombre
    tacos_por_columna["score"] = score
    return tacos_por_columna

def trasponer_3(tacos):
    return pd.DataFrame(tacos)

NUMBER = 10000
# measure trasponer 1
tiempo = timeit(
    "trasponer_1(tacos)",
    globals=globals(),
    number=NUMBER
)
print("trasponer_1", tiempo)

# measure trasponer 2
tiempo = timeit(
    "trasponer_2(tacos)",
    globals=globals(),
    number=NUMBER
)

print("trasponer_2", tiempo)

# measure trasponer 3
tiempo = timeit(
    "trasponer_3(tacos)",
    globals=globals(),
    number=NUMBER
)

print("trasponer_3", tiempo)