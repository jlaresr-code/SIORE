from dataclasses import dataclass
from typing import List, Optional
import copy

from standard_form import FormaEstandar


TOLERANCIA = 1e-9


@dataclass
class IteracionSimplex:
    numero: int
    tabla: List[List[float]]
    lados_derechos: List[float]
    base: List[str]
    no_basicas: List[str]
    cb: List[float]
    zj: List[float]
    cj_zj: List[float]
    variable_entrante: Optional[str]
    variable_saliente: Optional[str]
    razones: List[Optional[float]]
    pivote: Optional[float]
    valor_z: float


@dataclass
class ResultadoSimplex:
    estado: str
    solucion: dict
    valor_objetivo: Optional[float]
    iteraciones: List[IteracionSimplex]
    variables: List[str]


class Simplex:
    def __init__(
        self,
        forma: FormaEstandar
    ):
        if forma.variables_artificiales:
            raise ValueError(
                "El modelo contiene variables artificiales. "
                "Este módulo ejecuta Simplex primal directo."
            )

        self.forma = forma

        self.variables = list(
            forma.variables
        )

        self.a = copy.deepcopy(
            forma.matriz
        )

        self.b = list(
            forma.lados_derechos
        )

        self.c_original = list(
            forma.coef_objetivo
        )

        if forma.tipo_objetivo == "max":
            self.c = list(
                forma.coef_objetivo
            )
        else:
            self.c = [
                -coef
                for coef in forma.coef_objetivo
            ]

        self.base = [
            self.variables.index(nombre)
            for nombre in forma.base_inicial
        ]

        self.iteraciones = []

    def calcular_cb(self):
        return [
            self.c[indice]
            for indice in self.base
        ]

    def calcular_zj(
        self,
        cb
    ):
        zj = []

        for j in range(
            len(self.variables)
        ):
            valor = sum(
                cb[i] * self.a[i][j]
                for i in range(
                    len(self.a)
                )
            )

            zj.append(valor)

        return zj

    def calcular_cj_zj(
        self,
        zj
    ):
        return [
            self.c[j] - zj[j]
            for j in range(
                len(self.variables)
            )
        ]

    def calcular_z(
        self,
        cb
    ):
        return sum(
            cb[i] * self.b[i]
            for i in range(
                len(self.b)
            )
        )

    def obtener_no_basicas(self):
        return [
            self.variables[i]
            for i in range(
                len(self.variables)
            )
            if i not in self.base
        ]

    def seleccionar_entrante(
        self,
        cj_zj
    ):
        candidatos = [
            i
            for i, valor in enumerate(cj_zj)
            if valor > TOLERANCIA
        ]

        if not candidatos:
            return None

        return max(
            candidatos,
            key=lambda i: cj_zj[i]
        )

    def calcular_razones(
        self,
        columna_entrante
    ):
        razones = []

        for i in range(len(self.a)):
            coeficiente = self.a[i][
                columna_entrante
            ]

            if coeficiente > TOLERANCIA:
                razon = (
                    self.b[i]
                    / coeficiente
                )

                razones.append(razon)
            else:
                razones.append(None)

        return razones

    def seleccionar_saliente(
        self,
        razones
    ):
        candidatos = [
            (i, razon)
            for i, razon in enumerate(razones)
            if razon is not None
            and razon >= -TOLERANCIA
        ]

        if not candidatos:
            return None

        fila, _ = min(
            candidatos,
            key=lambda dato: (
                dato[1],
                dato[0]
            )
        )

        return fila

    def limpiar_valor(
        self,
        valor
    ):
        if abs(valor) <= TOLERANCIA:
            return 0.0

        return valor

    def pivotear(
        self,
        fila_pivote,
        columna_pivote
    ):
        pivote = self.a[
            fila_pivote
        ][
            columna_pivote
        ]

        if abs(pivote) <= TOLERANCIA:
            raise ZeroDivisionError(
                "El elemento pivote no puede ser cero."
            )

        self.a[fila_pivote] = [
            self.limpiar_valor(
                valor / pivote
            )
            for valor in self.a[
                fila_pivote
            ]
        ]

        self.b[fila_pivote] = (
            self.limpiar_valor(
                self.b[fila_pivote]
                / pivote
            )
        )

        for i in range(len(self.a)):
            if i == fila_pivote:
                continue

            factor = self.a[i][
                columna_pivote
            ]

            if abs(factor) <= TOLERANCIA:
                continue

            nueva_fila = []

            for j in range(
                len(self.variables)
            ):
                nuevo = (
                    self.a[i][j]
                    - factor
                    * self.a[fila_pivote][j]
                )

                nueva_fila.append(
                    self.limpiar_valor(
                        nuevo
                    )
                )

            self.a[i] = nueva_fila

            nuevo_ld = (
                self.b[i]
                - factor
                * self.b[fila_pivote]
            )

            self.b[i] = (
                self.limpiar_valor(
                    nuevo_ld
                )
            )

        self.base[
            fila_pivote
        ] = columna_pivote

    def guardar_iteracion(
        self,
        numero,
        cb,
        zj,
        cj_zj,
        entrante=None,
        saliente=None,
        razones=None,
        pivote=None
    ):
        base_nombres = [
            self.variables[indice]
            for indice in self.base
        ]

        iteracion = IteracionSimplex(
            numero=numero,
            tabla=copy.deepcopy(
                self.a
            ),
            lados_derechos=list(
                self.b
            ),
            base=base_nombres,
            no_basicas=self.obtener_no_basicas(),
            cb=list(cb),
            zj=list(zj),
            cj_zj=list(cj_zj),
            variable_entrante=entrante,
            variable_saliente=saliente,
            razones=(
                list(razones)
                if razones is not None
                else []
            ),
            pivote=pivote,
            valor_z=self.calcular_z(
                cb
            )
        )

        self.iteraciones.append(
            iteracion
        )

    def obtener_solucion(self):
        solucion = {
            variable: 0.0
            for variable in self.variables
        }

        for fila, indice in enumerate(
            self.base
        ):
            nombre = self.variables[
                indice
            ]

            solucion[nombre] = (
                self.limpiar_valor(
                    self.b[fila]
                )
            )

        return solucion

    def calcular_valor_original(
        self,
        solucion
    ):
        valor = 0.0

        for i, variable in enumerate(
            self.variables
        ):
            valor += (
                self.c_original[i]
                * solucion[variable]
            )

        return self.limpiar_valor(
            valor
        )

    def resolver(
        self,
        max_iteraciones=100
    ):
        for numero in range(
            max_iteraciones + 1
        ):
            cb = self.calcular_cb()
            zj = self.calcular_zj(cb)
            cj_zj = self.calcular_cj_zj(zj)

            columna_entrante = (
                self.seleccionar_entrante(
                    cj_zj
                )
            )

            if columna_entrante is None:
                self.guardar_iteracion(
                    numero=numero,
                    cb=cb,
                    zj=zj,
                    cj_zj=cj_zj
                )

                solucion = (
                    self.obtener_solucion()
                )

                valor_original = (
                    self.calcular_valor_original(
                        solucion
                    )
                )

                return ResultadoSimplex(
                    estado="Óptimo",
                    solucion=solucion,
                    valor_objetivo=valor_original,
                    iteraciones=self.iteraciones,
                    variables=self.variables
                )

            razones = (
                self.calcular_razones(
                    columna_entrante
                )
            )

            fila_saliente = (
                self.seleccionar_saliente(
                    razones
                )
            )

            if fila_saliente is None:
                self.guardar_iteracion(
                    numero=numero,
                    cb=cb,
                    zj=zj,
                    cj_zj=cj_zj,
                    entrante=self.variables[
                        columna_entrante
                    ],
                    razones=razones
                )

                return ResultadoSimplex(
                    estado="No acotado",
                    solucion={},
                    valor_objetivo=None,
                    iteraciones=self.iteraciones,
                    variables=self.variables
                )

            entrante = self.variables[
                columna_entrante
            ]

            saliente = self.variables[
                self.base[
                    fila_saliente
                ]
            ]

            pivote = self.a[
                fila_saliente
            ][
                columna_entrante
            ]

            self.guardar_iteracion(
                numero=numero,
                cb=cb,
                zj=zj,
                cj_zj=cj_zj,
                entrante=entrante,
                saliente=saliente,
                razones=razones,
                pivote=pivote
            )

            self.pivotear(
                fila_saliente,
                columna_entrante
            )

        return ResultadoSimplex(
            estado="Límite de iteraciones alcanzado",
            solucion={},
            valor_objetivo=None,
            iteraciones=self.iteraciones,
            variables=self.variables
        )


def formatear_numero(
    valor
):
    if valor is None:
        return "-"

    if abs(valor) < 1e-9:
        valor = 0.0

    return f"{valor:.4f}"


def mostrar_resultado_simplex(
    resultado
):
    print("\n" + "=" * 100)
    print("MÉTODO SIMPLEX")
    print("=" * 100)

    for iteracion in resultado.iteraciones:
        print(
            f"\nITERACIÓN {iteracion.numero}"
        )

        print("-" * 100)

        print(
            "Base:",
            ", ".join(
                iteracion.base
            )
        )

        print(
            "No básicas:",
            ", ".join(
                iteracion.no_basicas
            )
        )

        encabezado = (
            ["Base", "CB"]
            + resultado.variables
            + ["LD"]
        )

        print()

        print(
            "".join(
                f"{texto:>12}"
                for texto in encabezado
            )
        )

        for i, fila in enumerate(
            iteracion.tabla
        ):
            datos = (
                [
                    iteracion.base[i],
                    iteracion.cb[i]
                ]
                + fila
                + [
                    iteracion.lados_derechos[i]
                ]
            )

            salida = ""

            for valor in datos:
                if isinstance(
                    valor,
                    str
                ):
                    salida += (
                        f"{valor:>12}"
                    )
                else:
                    salida += (
                        f"{formatear_numero(valor):>12}"
                    )

            print(salida)

        print("\nZj:")

        print(
            {
                variable: round(valor, 4)
                for variable, valor in zip(
                    resultado.variables,
                    iteracion.zj
                )
            }
        )

        print("\nCj - Zj:")

        print(
            {
                variable: round(valor, 4)
                for variable, valor in zip(
                    resultado.variables,
                    iteracion.cj_zj
                )
            }
        )

        print(
            "\nValor actual Z:",
            round(
                iteracion.valor_z,
                4
            )
        )

        if iteracion.variable_entrante:
            print(
                "\nVariable entrante:",
                iteracion.variable_entrante
            )

            print(
                "Razones:",
                [
                    (
                        round(valor, 4)
                        if valor is not None
                        else None
                    )
                    for valor in iteracion.razones
                ]
            )

            print(
                "Variable saliente:",
                iteracion.variable_saliente
            )

            print(
                "Elemento pivote:",
                round(
                    iteracion.pivote,
                    4
                )
            )

        else:
            print(
                "\nNo existe variable entrante."
            )

            print(
                "Se alcanzó la optimalidad."
            )

    print("\n" + "=" * 100)

    print(
        "ESTADO:",
        resultado.estado
    )

    if resultado.solucion:
        print("\nSOLUCIÓN:")

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

    print("=" * 100)