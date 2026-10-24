from dataclasses import dataclass
from typing import List
from model import ModeloPL, formatear_expresion


@dataclass
class FormaEstandar:
    variables: List[str]
    coef_objetivo: List[float]
    matriz: List[List[float]]
    lados_derechos: List[float]
    base_inicial: List[str]
    variables_artificiales: List[str]
    tipo_objetivo: str

    def mostrar(self):
        print("\n" + "=" * 70)
        print("FORMA ESTÁNDAR")
        print("=" * 70)

        print("\nVariables:")
        print(", ".join(self.variables))

        tipo = (
            "Maximizar"
            if self.tipo_objetivo == "max"
            else "Minimizar"
        )

        funcion = formatear_expresion(
            self.coef_objetivo,
            self.variables
        )

        print("\nFunción objetivo extendida:")
        print(f"{tipo} Z = {funcion}")

        print("\nRestricciones transformadas:")

        for i, fila in enumerate(
            self.matriz,
            start=1
        ):
            expresion = formatear_expresion(
                fila,
                self.variables
            )

            print(
                f"R{i}: {expresion} "
                f"= {self.lados_derechos[i - 1]:g}"
            )

        print("\nBase inicial:")
        print(", ".join(self.base_inicial))

        if self.variables_artificiales:
            print("\nVariables artificiales:")
            print(", ".join(self.variables_artificiales))
        else:
            print("\nNo se requieren variables artificiales.")

        print("=" * 70)


def invertir_operador(operador):
    if operador == "<=":
        return ">="

    if operador == ">=":
        return "<="

    return "="


def convertir_a_forma_estandar(
    modelo: ModeloPL
) -> FormaEstandar:

    modelo.validar()

    restricciones = []

    for restriccion in modelo.restricciones:
        coeficientes = list(
            restriccion.coeficientes
        )

        operador = restriccion.operador
        ld = restriccion.lado_derecho

        if ld < 0:
            coeficientes = [
                -coef
                for coef in coeficientes
            ]

            ld = -ld
            operador = invertir_operador(
                operador
            )

        restricciones.append(
            {
                "coeficientes": coeficientes,
                "operador": operador,
                "ld": ld
            }
        )

    variables_originales = list(
        modelo.variables
    )

    variables_auxiliares = []
    informacion_auxiliar = []

    contador_holgura = 1
    contador_exceso = 1
    contador_artificial = 1

    base_inicial = []
    artificiales = []

    for restriccion in restricciones:
        operador = restriccion["operador"]

        datos = {
            "holgura": None,
            "exceso": None,
            "artificial": None
        }

        if operador == "<=":
            nombre = f"s{contador_holgura}"
            contador_holgura += 1

            variables_auxiliares.append(nombre)
            datos["holgura"] = nombre
            base_inicial.append(nombre)

        elif operador == ">=":
            exceso = f"e{contador_exceso}"
            contador_exceso += 1

            artificial = f"a{contador_artificial}"
            contador_artificial += 1

            variables_auxiliares.append(exceso)
            variables_auxiliares.append(artificial)

            datos["exceso"] = exceso
            datos["artificial"] = artificial

            base_inicial.append(artificial)
            artificiales.append(artificial)

        elif operador == "=":
            artificial = f"a{contador_artificial}"
            contador_artificial += 1

            variables_auxiliares.append(artificial)

            datos["artificial"] = artificial

            base_inicial.append(artificial)
            artificiales.append(artificial)

        informacion_auxiliar.append(datos)

    todas_variables = (
        variables_originales
        + variables_auxiliares
    )

    matriz = []
    lados_derechos = []

    for restriccion, auxiliares in zip(
        restricciones,
        informacion_auxiliar
    ):
        fila = [
            0.0
            for _ in todas_variables
        ]

        for i, coef in enumerate(
            restriccion["coeficientes"]
        ):
            fila[i] = float(coef)

        if auxiliares["holgura"]:
            indice = todas_variables.index(
                auxiliares["holgura"]
            )
            fila[indice] = 1.0

        if auxiliares["exceso"]:
            indice = todas_variables.index(
                auxiliares["exceso"]
            )
            fila[indice] = -1.0

        if auxiliares["artificial"]:
            indice = todas_variables.index(
                auxiliares["artificial"]
            )
            fila[indice] = 1.0

        matriz.append(fila)
        lados_derechos.append(
            float(restriccion["ld"])
        )

    coef_objetivo = [
        float(valor)
        for valor in modelo.coef_objetivo
    ]

    cantidad_auxiliares = (
        len(todas_variables)
        - len(variables_originales)
    )

    coef_objetivo.extend(
        [0.0] * cantidad_auxiliares
    )

    return FormaEstandar(
        variables=todas_variables,
        coef_objetivo=coef_objetivo,
        matriz=matriz,
        lados_derechos=lados_derechos,
        base_inicial=base_inicial,
        variables_artificiales=artificiales,
        tipo_objetivo=modelo.tipo_objetivo
    )