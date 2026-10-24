from dataclasses import dataclass
from typing import Dict, List, Optional

import pulp

from model import ModeloPL


TOLERANCIA = 1e-6


@dataclass
class ResultadoRestriccion:
    nombre: str
    operador: str
    lado_izquierdo: float
    lado_derecho: float
    holgura: float
    cumple: bool


@dataclass
class ResultadoPuLP:
    estado: str
    solucion: Dict[str, float]
    valor_objetivo: Optional[float]
    restricciones: List[ResultadoRestriccion]


def traducir_estado(estado_pulp):
    equivalencias = {
        "Optimal": "Óptimo",
        "Infeasible": "No factible",
        "Unbounded": "No acotado",
        "Undefined": "Indefinido",
        "Not Solved": "No resuelto"
    }

    return equivalencias.get(
        estado_pulp,
        estado_pulp
    )


def calcular_holgura(
    operador,
    lado_izquierdo,
    lado_derecho
):
    if operador == "<=":
        return lado_derecho - lado_izquierdo

    if operador == ">=":
        return lado_izquierdo - lado_derecho

    return abs(
        lado_izquierdo
        - lado_derecho
    )


def verificar_restriccion(
    operador,
    lado_izquierdo,
    lado_derecho
):
    if operador == "<=":
        return (
            lado_izquierdo
            <= lado_derecho + TOLERANCIA
        )

    if operador == ">=":
        return (
            lado_izquierdo
            >= lado_derecho - TOLERANCIA
        )

    return (
        abs(
            lado_izquierdo
            - lado_derecho
        )
        <= TOLERANCIA
    )


def resolver_con_pulp(
    modelo: ModeloPL
) -> ResultadoPuLP:

    modelo.validar()

    if modelo.tipo_objetivo == "max":
        sentido = pulp.LpMaximize
    else:
        sentido = pulp.LpMinimize

    problema = pulp.LpProblem(
        modelo.nombre.replace(" ", "_"),
        sentido
    )

    limite_inferior = (
        0
        if modelo.no_negatividad
        else None
    )

    variables_pulp = {}

    for nombre in modelo.variables:
        variables_pulp[nombre] = (
            pulp.LpVariable(
                nombre,
                lowBound=limite_inferior,
                cat="Continuous"
            )
        )

    funcion_objetivo = pulp.lpSum(
        coef
        * variables_pulp[nombre]

        for coef, nombre in zip(
            modelo.coef_objetivo,
            modelo.variables
        )
    )

    problema += funcion_objetivo

    for indice, restriccion in enumerate(
        modelo.restricciones,
        start=1
    ):
        expresion = pulp.lpSum(
            coef
            * variables_pulp[nombre]

            for coef, nombre in zip(
                restriccion.coeficientes,
                modelo.variables
            )
        )

        nombre_restriccion = (
            f"R{indice}"
        )

        if restriccion.operador == "<=":
            problema += (
                expresion
                <= restriccion.lado_derecho,
                nombre_restriccion
            )

        elif restriccion.operador == ">=":
            problema += (
                expresion
                >= restriccion.lado_derecho,
                nombre_restriccion
            )

        else:
            problema += (
                expresion
                == restriccion.lado_derecho,
                nombre_restriccion
            )

    solver = pulp.PULP_CBC_CMD(
        msg=False
    )

    problema.solve(
        solver
    )

    estado_original = pulp.LpStatus[
        problema.status
    ]

    estado = traducir_estado(
        estado_original
    )

    solucion = {}

    for nombre in modelo.variables:
        valor = variables_pulp[
            nombre
        ].value()

        solucion[nombre] = (
            0.0
            if valor is None
            else float(valor)
        )

    valor_objetivo = None

    if estado == "Óptimo":
        valor_objetivo = float(
            pulp.value(
                problema.objective
            )
        )

    resultados_restricciones = []

    for indice, restriccion in enumerate(
        modelo.restricciones,
        start=1
    ):
        lado_izquierdo = sum(
            coef
            * solucion[nombre]

            for coef, nombre in zip(
                restriccion.coeficientes,
                modelo.variables
            )
        )

        holgura = calcular_holgura(
            restriccion.operador,
            lado_izquierdo,
            restriccion.lado_derecho
        )

        if abs(holgura) <= TOLERANCIA:
            holgura = 0.0

        cumple = verificar_restriccion(
            restriccion.operador,
            lado_izquierdo,
            restriccion.lado_derecho
        )

        resultados_restricciones.append(
            ResultadoRestriccion(
                nombre=f"R{indice}",
                operador=restriccion.operador,
                lado_izquierdo=lado_izquierdo,
                lado_derecho=restriccion.lado_derecho,
                holgura=holgura,
                cumple=cumple
            )
        )

    return ResultadoPuLP(
        estado=estado,
        solucion=solucion,
        valor_objetivo=valor_objetivo,
        restricciones=resultados_restricciones
    )


def mostrar_resultado_pulp(
    resultado: ResultadoPuLP
):
    print("\n" + "=" * 80)
    print("RESULTADO PULP")
    print("=" * 80)

    print(
        "\nEstado:",
        resultado.estado
    )

    if resultado.solucion:
        print("\nSolución:")

        for variable, valor in (
            resultado.solucion.items()
        ):
            print(
                f"{variable} = "
                f"{valor:.4f}"
            )

    if resultado.valor_objetivo is not None:
        print(
            "\nValor óptimo Z =",
            f"{resultado.valor_objetivo:.4f}"
        )

    print("\nRestricciones:")

    for restriccion in (
        resultado.restricciones
    ):
        print(
            f"{restriccion.nombre}: "
            f"{restriccion.lado_izquierdo:.4f} "
            f"{restriccion.operador} "
            f"{restriccion.lado_derecho:.4f} "
            f"| Holgura = "
            f"{restriccion.holgura:.4f} "
            f"| Cumple = "
            f"{restriccion.cumple}"
        )

    print("=" * 80)