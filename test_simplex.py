from model import ModeloPL
from standard_form import convertir_a_forma_estandar
from simplex import Simplex


def probar_modelo_principal():
    modelo = ModeloPL(
        nombre="Prueba principal",
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

    forma = convertir_a_forma_estandar(
        modelo
    )

    solver = Simplex(
        forma
    )

    resultado = solver.resolver()

    assert resultado.estado == "Óptimo"
    assert abs(resultado.solucion["x1"] - 10) < 1e-6
    assert abs(resultado.solucion["x2"] - 10) < 1e-6
    assert abs(resultado.solucion["x3"] - 10) < 1e-6
    assert abs(resultado.valor_objetivo - 25000) < 1e-6

    print("PRUEBA 1: CORRECTA")
    print("x1 =", resultado.solucion["x1"])
    print("x2 =", resultado.solucion["x2"])
    print("x3 =", resultado.solucion["x3"])
    print("Z =", resultado.valor_objetivo)


def probar_modelo_simple():
    modelo = ModeloPL(
        nombre="Prueba secundaria",
        tipo_objetivo="max",
        variables=["x1", "x2"],
        coef_objetivo=[3, 5]
    )

    modelo.agregar_restriccion(
        [1, 0],
        "<=",
        4
    )

    modelo.agregar_restriccion(
        [0, 2],
        "<=",
        12
    )

    modelo.agregar_restriccion(
        [3, 2],
        "<=",
        18
    )

    forma = convertir_a_forma_estandar(
        modelo
    )

    solver = Simplex(
        forma
    )

    resultado = solver.resolver()

    assert resultado.estado == "Óptimo"
    assert abs(resultado.solucion["x1"] - 2) < 1e-6
    assert abs(resultado.solucion["x2"] - 6) < 1e-6
    assert abs(resultado.valor_objetivo - 36) < 1e-6

    print("\nPRUEBA 2: CORRECTA")
    print("x1 =", resultado.solucion["x1"])
    print("x2 =", resultado.solucion["x2"])
    print("Z =", resultado.valor_objetivo)


if __name__ == "__main__":
    probar_modelo_principal()
    probar_modelo_simple()

    print("\nTODAS LAS PRUEBAS FUERON SUPERADAS")