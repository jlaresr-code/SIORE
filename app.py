import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from model import ModeloPL, formatear_expresion
from standard_form import convertir_a_forma_estandar
from simplex import Simplex
from pulp_solver import resolver_con_pulp
from comparison import comparar_metodos
from scenarios import resolver_escenario


st.set_page_config(
    page_title="SIORE",
    page_icon="📊",
    layout="wide"
)


def imagen_base64(ruta):
    archivo = Path(ruta)
    if not archivo.exists():
        return None
    return base64.b64encode(archivo.read_bytes()).decode("utf-8")


fondo_b64 = imagen_base64("static/fondo.png")

if fondo_b64:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(
                    rgba(5, 10, 20, 0.55),
                    rgba(5, 10, 20, 0.65)
                ),
                url("data:image/png;base64,{fondo_b64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        .creditos-siore {{
            position: fixed;
            right: 22px;
            top: 82px;
            z-index: 9999;
            background: rgba(8, 15, 30, 0.82);
            border: 1px solid rgba(59, 130, 246, 0.40);
            border-radius: 14px;
            padding: 14px 18px;
            backdrop-filter: blur(8px);
            color: #F8FAFC;
            font-size: 12px;
            line-height: 1.55;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.30);
        }}

        .creditos-siore .carnet {{
            color: #94A3B8;
            font-size: 11px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <div class="creditos-siore">
        Bryan Colindres<br>
        <span class="carnet">6590-24-11396</span><br><br>
        Enrique Martínez<br>
        <span class="carnet">6590-24-9463</span><br><br>
        Jonathan Lares<br>
        <span class="carnet">6590-19-2133</span>
    </div>
    """,
    unsafe_allow_html=True
)


if "modelo" not in st.session_state:
    st.session_state.modelo = None

if "forma" not in st.session_state:
    st.session_state.forma = None

if "resultado_pulp" not in st.session_state:
    st.session_state.resultado_pulp = None

if "resultado_simplex" not in st.session_state:
    st.session_state.resultado_simplex = None

if "comparacion" not in st.session_state:
    st.session_state.comparacion = None

if "historial_escenarios" not in st.session_state:
    st.session_state.historial_escenarios = []

if "modelo_version" not in st.session_state:
    st.session_state.modelo_version = 0


col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    logo = Path("static/logo_umg.png")
    if logo.exists():
        st.image(str(logo), width=140)

with col_titulo:
    st.title("SIORE")
    st.subheader("Sistema Inteligente de Optimización de Recursos")
    st.caption(
        "Universidad Mariano Gálvez de Guatemala · "
        "Programación Lineal · Simplex propio · PuLP · Análisis de escenarios"
    )


def valor_defecto_objetivo(indice):
    valores = [900.0, 800.0, 800.0]
    return valores[indice] if indice < len(valores) else 0.0


def valor_defecto_restriccion(fila, columna):
    matriz = [
        [4.0, 3.0, 5.0],
        [2.0, 4.0, 1.0],
        [3.0, 1.0, 2.0]
    ]

    if fila < len(matriz) and columna < len(matriz[fila]):
        return matriz[fila][columna]

    return 0.0


def valor_defecto_ld(indice):
    valores = [120.0, 70.0, 60.0]
    return valores[indice] if indice < len(valores) else 0.0


def crear_modelo_texto(nombre, tipo, variables, objetivo, restricciones):
    encabezado = "Maximizar" if tipo == "max" else "Minimizar"
    lineas = [nombre, "", f"{encabezado} Z = {formatear_expresion(objetivo, variables)}", "", "Sujeto a:"]

    for i, datos in enumerate(restricciones, start=1):
        expresion = formatear_expresion(datos["coeficientes"], variables)
        lineas.append(f"R{i}: {expresion} {datos['operador']} {datos['ld']:g}")

    lineas.append("")
    lineas.append(", ".join(variables) + " >= 0")
    return "\n".join(lineas)


def crear_interpretacion(modelo, resultado):
    if resultado.estado != "Óptimo":
        return f"El modelo terminó con estado {resultado.estado}. No se dispone de una solución óptima para interpretar."

    valores = []

    for variable in modelo.variables:
        valor = resultado.solucion.get(variable, 0.0)
        valores.append(f"{variable} = {valor:,.2f}")

    activas = []

    for restriccion in resultado.restricciones:
        if abs(restriccion.holgura) <= 1e-6:
            activas.append(restriccion.nombre)

    texto = (
        "La solución óptima asigna "
        + ", ".join(valores)
        + f". El valor óptimo de la función objetivo es {resultado.valor_objetivo:,.2f}."
    )

    if activas:
        texto += " Las restricciones " + ", ".join(activas) + " se encuentran activas, sin holgura disponible."
    else:
        texto += " Ninguna restricción se encuentra completamente saturada."

    return texto


def tabla_forma_estandar(forma):
    datos = []

    for i, fila in enumerate(forma.matriz):
        registro = {variable: fila[j] for j, variable in enumerate(forma.variables)}
        registro["LD"] = forma.lados_derechos[i]
        datos.append(registro)

    return pd.DataFrame(datos, index=[f"R{i + 1}" for i in range(len(datos))])


def tabla_iteracion(iteracion, variables):
    datos = []

    for i, fila in enumerate(iteracion.tabla):
        registro = {
            "Base": iteracion.base[i],
            "CB": iteracion.cb[i]
        }

        for j, variable in enumerate(variables):
            registro[variable] = fila[j]

        registro["LD"] = iteracion.lados_derechos[i]
        datos.append(registro)

    return pd.DataFrame(datos)


def resolver_modelo(modelo):
    forma = convertir_a_forma_estandar(modelo)
    resultado_pulp = resolver_con_pulp(modelo)
    resultado_simplex = None
    comparacion = None

    if not forma.variables_artificiales:
        resultado_simplex = Simplex(forma).resolver()

        try:
            comparacion = comparar_metodos(modelo)
        except Exception:
            comparacion = None

    return forma, resultado_pulp, resultado_simplex, comparacion


pestana_modelo, pestana_resultados, pestana_simplex, pestana_escenarios = st.tabs(
    ["🧮 Modelo", "📊 Resultados", "🔢 Simplex", "🔄 Escenarios"]
)


with pestana_modelo:
    st.header("Definición del problema")

    columna_a, columna_b, columna_c = st.columns([2, 1, 1])

    with columna_a:
        nombre_problema = st.text_input(
            "Nombre del problema",
            value="Optimización de Servicios Tecnológicos"
        )

    with columna_b:
        tipo_visible = st.selectbox(
            "Objetivo",
            ["Maximizar", "Minimizar"]
        )

    with columna_c:
        no_negatividad = st.checkbox(
            "No negatividad",
            value=True
        )

    columna_d, columna_e = st.columns(2)

    with columna_d:
        cantidad_variables = int(
            st.number_input(
                "Cantidad de variables",
                min_value=3,
                value=3,
                step=1
            )
        )

    with columna_e:
        cantidad_restricciones = int(
            st.number_input(
                "Cantidad de restricciones",
                min_value=3,
                value=3,
                step=1
            )
        )

    st.subheader("Variables de decisión")

    nombres_variables = []

    for inicio in range(0, cantidad_variables, 4):
        cantidad_fila = min(4, cantidad_variables - inicio)
        columnas = st.columns(cantidad_fila)

        for posicion in range(cantidad_fila):
            indice = inicio + posicion

            with columnas[posicion]:
                nombre_variable = st.text_input(
                    f"Variable {indice + 1}",
                    value=f"x{indice + 1}",
                    key=f"nombre_variable_{indice}"
                ).strip()

                nombres_variables.append(nombre_variable)

    st.subheader("Función objetivo")

    coeficientes_objetivo = []

    for inicio in range(0, cantidad_variables, 4):
        cantidad_fila = min(4, cantidad_variables - inicio)
        columnas = st.columns(cantidad_fila)

        for posicion in range(cantidad_fila):
            indice = inicio + posicion

            with columnas[posicion]:
                coeficiente = st.number_input(
                    f"Coeficiente de {nombres_variables[indice] or f'x{indice + 1}'}",
                    value=float(valor_defecto_objetivo(indice)),
                    step=1.0,
                    key=f"objetivo_{indice}"
                )

                coeficientes_objetivo.append(float(coeficiente))

    st.subheader("Restricciones")

    restricciones_actuales = []

    for fila in range(cantidad_restricciones):
        st.markdown(f"**Restricción R{fila + 1}**")
        coeficientes = []

        for inicio in range(0, cantidad_variables, 4):
            cantidad_fila = min(4, cantidad_variables - inicio)
            columnas = st.columns(cantidad_fila)

            for posicion in range(cantidad_fila):
                columna = inicio + posicion

                with columnas[posicion]:
                    coeficiente = st.number_input(
                        f"{nombres_variables[columna] or f'x{columna + 1}'} en R{fila + 1}",
                        value=float(valor_defecto_restriccion(fila, columna)),
                        step=1.0,
                        key=f"restriccion_{fila}_{columna}"
                    )

                    coeficientes.append(float(coeficiente))

        columna_operador, columna_ld = st.columns([1, 2])

        with columna_operador:
            operador = st.selectbox(
                f"Operador R{fila + 1}",
                ["<=", ">=", "="],
                key=f"operador_{fila}"
            )

        with columna_ld:
            lado_derecho = st.number_input(
                f"Lado derecho R{fila + 1}",
                value=float(valor_defecto_ld(fila)),
                step=1.0,
                key=f"ld_{fila}"
            )

        restricciones_actuales.append(
            {
                "coeficientes": coeficientes,
                "operador": operador,
                "ld": float(lado_derecho)
            }
        )

        st.divider()

    tipo_objetivo = "max" if tipo_visible == "Maximizar" else "min"

    st.subheader("Vista previa del modelo matemático")

    st.code(
        crear_modelo_texto(
            nombre_problema,
            tipo_objetivo,
            nombres_variables,
            coeficientes_objetivo,
            restricciones_actuales
        ),
        language="text"
    )

    if st.button("Resolver modelo", type="primary", use_container_width=True):
        try:
            if not nombre_problema.strip():
                raise ValueError("Debes escribir un nombre para el problema.")

            if any(not nombre for nombre in nombres_variables):
                raise ValueError("Todos los nombres de variables deben estar completos.")

            if len(set(nombres_variables)) != len(nombres_variables):
                raise ValueError("Los nombres de las variables no pueden repetirse.")

            modelo = ModeloPL(
                nombre=nombre_problema.strip(),
                tipo_objetivo=tipo_objetivo,
                variables=nombres_variables,
                coef_objetivo=coeficientes_objetivo,
                no_negatividad=no_negatividad
            )

            for datos in restricciones_actuales:
                modelo.agregar_restriccion(
                    datos["coeficientes"],
                    datos["operador"],
                    datos["ld"]
                )

            forma, resultado_pulp, resultado_simplex, comparacion = resolver_modelo(modelo)

            st.session_state.modelo = modelo
            st.session_state.forma = forma
            st.session_state.resultado_pulp = resultado_pulp
            st.session_state.resultado_simplex = resultado_simplex
            st.session_state.comparacion = comparacion
            st.session_state.historial_escenarios = []
            st.session_state.modelo_version += 1

            st.success("Modelo procesado correctamente. Abre la pestaña Resultados para ver la solución.")

        except Exception as error:
            st.error(str(error))


with pestana_resultados:
    st.header("Dashboard de resultados")

    modelo = st.session_state.modelo
    resultado_pulp = st.session_state.resultado_pulp
    forma = st.session_state.forma
    comparacion = st.session_state.comparacion

    if modelo is None or resultado_pulp is None:
        st.info("Primero define y resuelve un modelo en la pestaña Modelo.")
    else:
        valor_z = "—" if resultado_pulp.valor_objetivo is None else f"{resultado_pulp.valor_objetivo:,.2f}"

        metrica_a, metrica_b, metrica_c, metrica_d = st.columns(4)
        metrica_a.metric("Estado", resultado_pulp.estado)
        metrica_b.metric("Valor objetivo Z", valor_z)
        metrica_c.metric("Variables", len(modelo.variables))
        metrica_d.metric("Restricciones", len(modelo.restricciones))

        st.subheader("Solución óptima")

        solucion_df = pd.DataFrame(
            {
                "Variable": modelo.variables,
                "Valor": [resultado_pulp.solucion.get(variable, 0.0) for variable in modelo.variables]
            }
        )

        columna_solucion, columna_grafica = st.columns([1, 2])

        with columna_solucion:
            st.dataframe(solucion_df, use_container_width=True, hide_index=True)

        with columna_grafica:
            st.bar_chart(solucion_df.set_index("Variable"))

        st.subheader("Uso y cumplimiento de restricciones")

        restricciones_df = pd.DataFrame(
            [
                {
                    "Restricción": restriccion.nombre,
                    "Lado izquierdo": restriccion.lado_izquierdo,
                    "Operador": restriccion.operador,
                    "Lado derecho": restriccion.lado_derecho,
                    "Holgura": restriccion.holgura,
                    "Cumple": "Sí" if restriccion.cumple else "No"
                }
                for restriccion in resultado_pulp.restricciones
            ]
        )

        st.dataframe(restricciones_df, use_container_width=True, hide_index=True)

        grafica_recursos = restricciones_df[
            ["Restricción", "Lado izquierdo", "Lado derecho"]
        ].set_index("Restricción")

        st.bar_chart(
            grafica_recursos,
            stack=False,
            use_container_width=True
        )

        st.subheader("Interpretación automática")
        st.info(crear_interpretacion(modelo, resultado_pulp))

        st.subheader("Comparación de métodos")

        if comparacion is not None:
            comparacion_df = pd.DataFrame(
                {
                    "Variable": modelo.variables,
                    "Simplex propio": [comparacion.variables_simplex[variable] for variable in modelo.variables],
                    "PuLP": [comparacion.variables_pulp[variable] for variable in modelo.variables]
                }
            )

            st.dataframe(comparacion_df, use_container_width=True, hide_index=True)

            columna_simplex_z, columna_pulp_z = st.columns(2)
            columna_simplex_z.metric("Z Simplex", f"{comparacion.valor_simplex:,.2f}")
            columna_pulp_z.metric("Z PuLP", f"{comparacion.valor_pulp:,.2f}")

            if comparacion.coincide:
                st.success("Los resultados del Simplex propio y PuLP coinciden.")
            else:
                st.warning("Los resultados del Simplex propio y PuLP no coinciden dentro de la tolerancia definida.")
        else:
            if forma.variables_artificiales:
                st.info(
                    "PuLP resolvió el modelo, pero el Simplex propio no se ejecutó porque la forma estándar requiere variables artificiales. "
                    "El módulo actual implementa Simplex primal directo para modelos compatibles."
                )
            else:
                st.info("No fue posible generar una comparación de métodos para este modelo.")

        with st.expander("Ver forma estándar"):
            st.write("Variables:", ", ".join(forma.variables))
            st.write("Base inicial:", ", ".join(forma.base_inicial))

            if forma.variables_artificiales:
                st.write("Variables artificiales:", ", ".join(forma.variables_artificiales))
            else:
                st.write("Variables artificiales: ninguna")

            st.dataframe(tabla_forma_estandar(forma), use_container_width=True)


with pestana_simplex:
    st.header("Iteraciones del Simplex propio")

    resultado_simplex = st.session_state.resultado_simplex
    forma = st.session_state.forma
    modelo = st.session_state.modelo

    if modelo is None:
        st.info("Primero define y resuelve un modelo en la pestaña Modelo.")
    elif resultado_simplex is None:
        if forma is not None and forma.variables_artificiales:
            st.warning(
                "Este modelo necesita variables artificiales y no es compatible con el Simplex primal directo implementado. "
                "La solución general se muestra mediante PuLP en la pestaña Resultados."
            )
        else:
            st.info("No hay iteraciones del Simplex disponibles.")
    else:
        columna_estado, columna_z, columna_iteraciones = st.columns(3)
        columna_estado.metric("Estado", resultado_simplex.estado)
        columna_z.metric(
            "Z Simplex",
            "—" if resultado_simplex.valor_objetivo is None else f"{resultado_simplex.valor_objetivo:,.2f}"
        )
        columna_iteraciones.metric("Iteraciones", len(resultado_simplex.iteraciones))

        for iteracion in resultado_simplex.iteraciones:
            with st.expander(f"Iteración {iteracion.numero}", expanded=iteracion.numero == 0):
                st.write("Variables básicas:", ", ".join(iteracion.base))
                st.write("Variables no básicas:", ", ".join(iteracion.no_basicas))

                if iteracion.variable_entrante is not None:
                    dato_a, dato_b, dato_c = st.columns(3)
                    dato_a.metric("Variable entrante", iteracion.variable_entrante)
                    dato_b.metric("Variable saliente", iteracion.variable_saliente or "—")
                    dato_c.metric("Pivote", f"{iteracion.pivote:,.4f}" if iteracion.pivote is not None else "—")
                else:
                    st.success("No existe variable entrante. Se alcanzó la optimalidad.")

                st.dataframe(
                    tabla_iteracion(iteracion, resultado_simplex.variables),
                    use_container_width=True,
                    hide_index=True
                )

                indicadores_df = pd.DataFrame(
                    {
                        "Variable": resultado_simplex.variables,
                        "Zj": iteracion.zj,
                        "Cj - Zj": iteracion.cj_zj
                    }
                )

                st.dataframe(indicadores_df, use_container_width=True, hide_index=True)

                if iteracion.razones:
                    razones_df = pd.DataFrame(
                        {
                            "Fila": [f"R{i + 1}" for i in range(len(iteracion.razones))],
                            "Razón": [valor if valor is not None else "No aplica" for valor in iteracion.razones]
                        }
                    )
                    st.dataframe(razones_df, use_container_width=True, hide_index=True)

        st.subheader("Solución final del Simplex")

        solucion_simplex_df = pd.DataFrame(
            {
                "Variable": list(resultado_simplex.solucion.keys()),
                "Valor": list(resultado_simplex.solucion.values())
            }
        )

        st.dataframe(solucion_simplex_df, use_container_width=True, hide_index=True)


with pestana_escenarios:
    st.header("Análisis de escenarios")

    modelo = st.session_state.modelo
    resultado_base = st.session_state.resultado_pulp

    if modelo is None or resultado_base is None:
        st.info("Primero define y resuelve un modelo en la pestaña Modelo.")
    else:
        st.write("Modifica los lados derechos de las restricciones para evaluar cambios en los recursos disponibles.")

        nombre_escenario = st.text_input(
            "Nombre del escenario",
            value="Escenario alternativo",
            key=f"nombre_escenario_{st.session_state.modelo_version}"
        )

        nuevos_recursos = []

        for i, restriccion in enumerate(modelo.restricciones):
            nuevo_valor = st.number_input(
                f"Nuevo lado derecho de R{i + 1}",
                value=float(restriccion.lado_derecho),
                step=1.0,
                key=f"escenario_{st.session_state.modelo_version}_{i}"
            )

            nuevos_recursos.append(float(nuevo_valor))

        if st.button("Evaluar escenario", type="primary", use_container_width=True):
            try:
                escenario = resolver_escenario(
                    modelo,
                    nombre_escenario.strip() or "Escenario alternativo",
                    nuevos_recursos
                )

                st.session_state.historial_escenarios.append(escenario)
                st.success("Escenario evaluado correctamente.")
            except Exception as error:
                st.error(str(error))

        filas_escenarios = []

        filas_escenarios.append(
            {
                "Escenario": "Escenario base",
                "Estado": resultado_base.estado,
                "Z": resultado_base.valor_objetivo
            }
        )

        for escenario in st.session_state.historial_escenarios:
            filas_escenarios.append(
                {
                    "Escenario": escenario.nombre,
                    "Estado": escenario.resultado.estado,
                    "Z": escenario.resultado.valor_objetivo
                }
            )

        escenarios_df = pd.DataFrame(filas_escenarios)

        st.subheader("Comparación")
        st.dataframe(escenarios_df, use_container_width=True, hide_index=True)

        escenarios_grafica = escenarios_df.dropna(subset=["Z"]).set_index("Escenario")

        if not escenarios_grafica.empty:
            st.bar_chart(escenarios_grafica[["Z"]])

        if st.session_state.historial_escenarios and resultado_base.valor_objetivo is not None:
            ultimo = st.session_state.historial_escenarios[-1]

            if ultimo.resultado.valor_objetivo is not None:
                cambio = ultimo.resultado.valor_objetivo - resultado_base.valor_objetivo

                columna_base, columna_nuevo, columna_cambio = st.columns(3)
                columna_base.metric("Z base", f"{resultado_base.valor_objetivo:,.2f}")
                columna_nuevo.metric("Z escenario", f"{ultimo.resultado.valor_objetivo:,.2f}")
                columna_cambio.metric("Cambio en Z", f"{cambio:,.2f}")

                if modelo.tipo_objetivo == "max":
                    if cambio > 1e-6:
                        st.success("El escenario mejora el valor de la función objetivo respecto al escenario base.")
                    elif cambio < -1e-6:
                        st.warning("El escenario reduce el valor de la función objetivo respecto al escenario base.")
                    else:
                        st.info("El escenario no modifica el valor óptimo de la función objetivo.")
                else:
                    if cambio < -1e-6:
                        st.success("El escenario reduce el valor de la función objetivo, lo cual mejora un problema de minimización.")
                    elif cambio > 1e-6:
                        st.warning("El escenario aumenta el valor de la función objetivo en el problema de minimización.")
                    else:
                        st.info("El escenario no modifica el valor óptimo de la función objetivo.")
