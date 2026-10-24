from dataclasses import dataclass, field
from typing import List


def formatear_expresion(coeficientes, variables):
    partes = []

    for coef, variable in zip(coeficientes, variables):
        if abs(coef) < 1e-12:
            continue

        valor = abs(coef)

        if valor == 1:
            termino = variable
        else:
            termino = f"{valor:g}{variable}"

        if not partes:
            partes.append(
                f"-{termino}" if coef < 0 else termino
            )
        else:
            signo = "-" if coef < 0 else "+"
            partes.append(f"{signo} {termino}")

    return " ".join(partes) if partes else "0"


@dataclass
class Restriccion:
    coeficientes: List[float]
    operador: str
    lado_derecho: float

    def validar(self):
        if self.operador not in ["<=", ">=", "="]:
            raise ValueError(
                "El operador debe ser <=, >= o ="
            )


@dataclass
class ModeloPL:
    nombre: str
    tipo_objetivo: str
    variables: List[str]
    coef_objetivo: List[float]
    restricciones: List[Restriccion] = field(default_factory=list)
    no_negatividad: bool = True

    def validar(self):
        if self.tipo_objetivo not in ["max", "min"]:
            raise ValueError(
                "El tipo de objetivo debe ser 'max' o 'min'."
            )

        if len(self.variables) == 0:
            raise ValueError(
                "El modelo debe tener al menos una variable."
            )

        if len(self.variables) != len(self.coef_objetivo):
            raise ValueError(
                "La cantidad de variables no coincide con los coeficientes de la función objetivo."
            )

        if len(set(self.variables)) != len(self.variables):
            raise ValueError(
                "Los nombres de las variables no pueden repetirse."
            )

        for restriccion in self.restricciones:
            restriccion.validar()

            if len(restriccion.coeficientes) != len(self.variables):
                raise ValueError(
                    "Una restricción tiene una cantidad incorrecta de coeficientes."
                )

        return True

    def agregar_restriccion(
        self,
        coeficientes,
        operador,
        lado_derecho
    ):
        if len(coeficientes) != len(self.variables):
            raise ValueError(
                "La cantidad de coeficientes debe coincidir con la cantidad de variables."
            )

        nueva = Restriccion(
            coeficientes=[
                float(valor)
                for valor in coeficientes
            ],
            operador=operador,
            lado_derecho=float(lado_derecho)
        )

        nueva.validar()
        self.restricciones.append(nueva)

    def mostrar_modelo(self):
        self.validar()

        print("\n" + "=" * 70)
        print(self.nombre)
        print("=" * 70)

        tipo = (
            "Maximizar"
            if self.tipo_objetivo == "max"
            else "Minimizar"
        )

        funcion = formatear_expresion(
            self.coef_objetivo,
            self.variables
        )

        print(f"\n{tipo}:")
        print(f"Z = {funcion}")

        print("\nSujeto a:")

        for i, restriccion in enumerate(
            self.restricciones,
            start=1
        ):
            expresion = formatear_expresion(
                restriccion.coeficientes,
                self.variables
            )

            print(
                f"R{i}: {expresion} "
                f"{restriccion.operador} "
                f"{restriccion.lado_derecho:g}"
            )

        if self.no_negatividad:
            print(
                "\n"
                + ", ".join(self.variables)
                + " >= 0"
            )

        print("=" * 70)