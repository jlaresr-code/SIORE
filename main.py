from model import ModeloPL
from standard_form import convertir_a_forma_estandar
from simplex import Simplex, mostrar_resultado_simplex


modelo = ModeloPL(
    nombre="Optimización de Servicios Tecnológicos",
    tipo_objetivo="max",
    variables=["x1", "x2", "x3"],
    coef_objetivo=[900, 800, 800]
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


modelo.mostrar_modelo()


forma_estandar = convertir_a_forma_estandar(
    modelo
)


forma_estandar.mostrar()


solver = Simplex(
    forma_estandar
)


resultado = solver.resolver()


mostrar_resultado_simplex(
    resultado
)