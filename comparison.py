from dataclasses import dataclass
from typing import Dict

from model import ModeloPL
from standard_form import convertir_a_forma_estandar
from simplex import Simplex
from pulp_solver import resolver_con_pulp


TOLERANCIA = 1e-6


@dataclass
class ResultadoComparacion:
    coincide: bool
    estado_simplex: str
    estado_pulp: str
    valor_simplex: float
    valor_pulp: float
    variables_simplex: Dict[str, float]
    variables_pulp: Dict[str, float]


def comparar_metodos(
    modelo: ModeloPL
) -> ResultadoComparacion:

    forma = convertir_a_forma_estandar(
        modelo
    )

    if forma.variables_artificiales:
        raise ValueError(
            "Este modelo no es compatible "
            "con el Simplex primal directo."
        )

    simplex = Simplex(
        forma
    )

    resultado_simplex = (
        simplex.resolver()
    )

    resultado_pulp = (
        resolver_con_pulp(
            modelo
        )
    )

    variables_simplex = {}

    for nombre in modelo.variables:
        variables_simplex[nombre] = (
            resultado_simplex.solucion.get(
                nombre,
                0.0
            )
        )

    variables_pulp = {}

    for nombre in modelo.variables:
        variables_pulp[nombre] = (
            resultado_pulp.solucion.get(
                nombre,
                0.0
            )
        )

    coincide = (
        resultado_simplex.estado
        == "Óptimo"
        and resultado_pulp.estado
        == "Óptimo"
    )

    if coincide:
        diferencia_z = abs(
            resultado_simplex.valor_objetivo
            - resultado_pulp.valor_objetivo
        )

        if diferencia_z > TOLERANCIA:
            coincide = False

    if coincide:
        for nombre in modelo.variables:
            diferencia = abs(
                variables_simplex[nombre]
                - variables_pulp[nombre]
            )

            if diferencia > TOLERANCIA:
                coincide = False
                break

    return ResultadoComparacion(
        coincide=coincide,
        estado_simplex=resultado_simplex.estado,
        estado_pulp=resultado_pulp.estado,
        valor_simplex=resultado_simplex.valor_objetivo,
        valor_pulp=resultado_pulp.valor_objetivo,
        variables_simplex=variables_simplex,
        variables_pulp=variables_pulp
    )


def mostrar_comparacion(
    resultado
):
    print("\n" + "=" * 80)
    print("COMPARACIÓN SIMPLEX PROPIO VS PULP")
    print("=" * 80)

    print(
        "\nEstado Simplex:",
        resultado.estado_simplex
    )

    print(
        "Estado PuLP:",
        resultado.estado_pulp
    )

    print(
        "\nValor Z Simplex:",
        resultado.valor_simplex
    )

    print(
        "Valor Z PuLP:",
        resultado.valor_pulp
    )

    print("\nVariables:")

    for nombre in (
        resultado.variables_simplex
    ):
        print(
            f"{nombre}: "
            f"Simplex = "
            f"{resultado.variables_simplex[nombre]:.4f}"
            f" | PuLP = "
            f"{resultado.variables_pulp[nombre]:.4f}"
        )

    print()

    if resultado.coincide:
        print(
            "RESULTADO: LOS DOS MÉTODOS COINCIDEN"
        )
    else:
        print(
            "RESULTADO: LOS MÉTODOS NO COINCIDEN"
        )

    print("=" * 80)