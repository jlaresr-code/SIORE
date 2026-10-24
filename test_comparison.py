from model import ModeloPL
from comparison import (
    comparar_metodos,
    mostrar_comparacion
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


resultado = comparar_metodos(
    modelo
)


mostrar_comparacion(
    resultado
)


assert resultado.coincide


print(
    "\nPRUEBA DE COMPARACIÓN SUPERADA"
)