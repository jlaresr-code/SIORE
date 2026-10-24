from model import ModeloPL
from pulp_solver import (
    resolver_con_pulp,
    mostrar_resultado_pulp
)


modelo = ModeloPL(
    nombre="Optimización de Servicios Tecnológicos",
    tipo_objetivo="max",
    variables=[
        "x1",
        "x2",
        "x3"
    ],
    coef_objetivo=[
        900,
        800,
        800
    ]
)


modelo.agregar_restriccion(
    [4, 3, 5],
    "<=",
    120
)

modelo.agregar_restriccion(
    [2, 4, 1],
    "<=",
    70
)

modelo.agregar_restriccion(
    [3, 1, 2],
    "<=",
    60
)


resultado = resolver_con_pulp(
    modelo
)


mostrar_resultado_pulp(
    resultado
)


assert resultado.estado == "Óptimo"

assert abs(
    resultado.solucion["x1"]
    - 10
) < 1e-6

assert abs(
    resultado.solucion["x2"]
    - 10
) < 1e-6

assert abs(
    resultado.solucion["x3"]
    - 10
) < 1e-6

assert abs(
    resultado.valor_objetivo
    - 25000
) < 1e-6


print(
    "\nPRUEBA PULP SUPERADA"
)