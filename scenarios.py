from dataclasses import dataclass
from typing import List

from model import ModeloPL
from pulp_solver import (
    ResultadoPuLP,
    resolver_con_pulp
)


@dataclass
class ResultadoEscenario:
    nombre: str
    recursos: List[float]
    resultado: ResultadoPuLP


def copiar_modelo_con_recursos(
    modelo: ModeloPL,
    nombre: str,
    nuevos_recursos: List[float]
) -> ModeloPL:

    if len(nuevos_recursos) != len(
        modelo.restricciones
    ):
        raise ValueError(
            "La cantidad de recursos debe "
            "coincidir con la cantidad de restricciones."
        )

    nuevo = ModeloPL(
        nombre=nombre,
        tipo_objetivo=modelo.tipo_objetivo,
        variables=list(
            modelo.variables
        ),
        coef_objetivo=list(
            modelo.coef_objetivo
        ),
        no_negatividad=(
            modelo.no_negatividad
        )
    )

    for restriccion, nuevo_ld in zip(
        modelo.restricciones,
        nuevos_recursos
    ):
        nuevo.agregar_restriccion(
            list(
                restriccion.coeficientes
            ),
            restriccion.operador,
            nuevo_ld
        )

    return nuevo


def resolver_escenario(
    modelo: ModeloPL,
    nombre: str,
    recursos: List[float]
) -> ResultadoEscenario:

    modelo_escenario = (
        copiar_modelo_con_recursos(
            modelo,
            nombre,
            recursos
        )
    )

    resultado = resolver_con_pulp(
        modelo_escenario
    )

    return ResultadoEscenario(
        nombre=nombre,
        recursos=recursos,
        resultado=resultado
    )


def comparar_escenarios(
    escenarios: List[ResultadoEscenario]
):
    print("\n" + "=" * 90)
    print("COMPARACIÓN DE ESCENARIOS")
    print("=" * 90)

    for escenario in escenarios:
        print(
            f"\n{escenario.nombre}"
        )

        print(
            "Recursos:",
            escenario.recursos
        )

        print(
            "Estado:",
            escenario.resultado.estado
        )

        print(
            "Z:",
            escenario.resultado.valor_objetivo
        )

        print(
            "Variables:",
            escenario.resultado.solucion
        )

    print("=" * 90)