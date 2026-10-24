from model import ModeloPL
from scenarios import (
    resolver_escenario,
    comparar_escenarios
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


base = resolver_escenario(
    modelo,
    "Escenario Base",
    [120, 70, 60]
)


aumento_desarrollo = (
    resolver_escenario(
        modelo,
        "Aumento de Desarrollo",
        [140, 70, 60]
    )
)


escenarios = [
    base,
    aumento_desarrollo
]


comparar_escenarios(
    escenarios
)


assert (
    base.resultado.estado
    == "Óptimo"
)

assert (
    aumento_desarrollo.resultado.estado
    == "Óptimo"
)

assert (
    aumento_desarrollo.resultado.valor_objetivo
    >= base.resultado.valor_objetivo
)


print(
    "\nPRUEBA DE ESCENARIOS SUPERADA"
)