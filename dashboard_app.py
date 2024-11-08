import streamlit as st
import pandas as pd

st.title("Cargar y procesar archivo CSV y Excel")
# Cargar archivo CSV sin nombres de columna
csv_file = st.file_uploader("Cargar archivo CSV", type=["csv"])
if csv_file is not None:
    # Leer el archivo CSV sin encabezado
    df_csv = pd.read_csv(csv_file, header=None, encoding='ISO-8859-1')
    
    # Asignar nombres de columnas según las detectadas
    column_names = ['CUENTA', 'SUCURSAL', 'Vacio', 'FECHA', 'Vacio2', 'VALOR', 'CODIGO', 'DESCRIPCION', 'ceros', 'extra']
    df_csv.columns = column_names[:df_csv.shape[1]]
    
    # Eliminar columnas innecesarias
    df_csv = df_csv.drop(columns=['Vacio', 'Vacio2', 'ceros', 'extra'], errors='ignore')
    
    # Convertir la columna FECHA a formato de fecha
    df_csv['FECHA'] = pd.to_datetime(df_csv['FECHA'], format='%Y%m%d', errors='coerce')
    # Separar VALOR en Entradas y Salidas
    df_csv['Entradas'] = df_csv['VALOR'].apply(lambda x: x if x > 0 else 0)
    df_csv['Salidas'] = df_csv['VALOR'].apply(lambda x: -x if x < 0 else 0)
    # Convertir las columnas Entradas y Salidas a tipo float
    df_csv['Entradas'] = pd.to_numeric(df_csv['Entradas'], errors='coerce')
    df_csv['Salidas'] = pd.to_numeric(df_csv['Salidas'], errors='coerce')
    st.write("Datos del CSV cargado:")
    st.write(f"Total de registros en CSV: {df_csv.shape[0]}")
    st.dataframe(df_csv)
# Cargar archivo Excel
excel_file = st.file_uploader("Cargar archivo Excel", type=["xlsx"])
if excel_file is not None:
    sheet_names = pd.ExcelFile(excel_file).sheet_names
    selected_sheet = st.selectbox("Selecciona la hoja de Excel", sheet_names)
    df_excel = pd.read_excel(excel_file, sheet_name=selected_sheet)
    # Convertir columnas Debito y Credito a tipo float
    df_excel['Debito'] = df_excel['Debito'].astype(float)
    df_excel['Credito'] = df_excel['Credito'].astype(float)
    # Inicializar listas para los registros cruzados y no cruzados
    registros_cruzados = []
    registros_no_cruzados = []
    # Marcar cada registro del Excel para uso único
    df_excel['cruzado'] = False
    st.write("Datos del Excel cargado:")
    st.write(f"Total de registros en Excel: {df_excel.shape[0]}")
    st.dataframe(df_excel)
    # Primer cruce directo entre CSV y Excel
    for idx_csv, row_csv in df_csv.iterrows():
        if row_csv['Entradas'] > 0:  # Buscar cruce en Debitos
            cruce_entrada = df_excel[(df_excel['Debito'] == row_csv['Entradas']) & (~df_excel['cruzado'])]
            if not cruce_entrada.empty:
                registro_excel = cruce_entrada.iloc[0]
                registros_cruzados.append(pd.concat([row_csv, registro_excel], axis=0))
                df_excel.at[registro_excel.name, 'cruzado'] = True
            else:
                registros_no_cruzados.append(row_csv)
        elif row_csv['Salidas'] > 0:  # Buscar cruce en Creditos
            cruce_salida = df_excel[(df_excel['Credito'] == row_csv['Salidas']) & (~df_excel['cruzado'])]
            if not cruce_salida.empty:
                registro_excel = cruce_salida.iloc[0]
                registros_cruzados.append(pd.concat([row_csv, registro_excel], axis=0))
                df_excel.at[registro_excel.name, 'cruzado'] = True
            else:
                registros_no_cruzados.append(row_csv)
       # Registros cruzados
df_cruzados = pd.DataFrame(registros_cruzados)
st.write("Registros cruzados (desde CSV hacia Excel):")
st.write(f"Cantidad de registros cruzados: {len(df_cruzados)}")
st.dataframe(df_cruzados)

# Definir DataFrame de no cruzados si no existe
df_csv_no_cruzados = pd.DataFrame(registros_no_cruzados)

# Mostrar los registros no cruzados
st.write("Registros no cruzados en el CSV:")
st.write(f"Cantidad de registros no cruzados en CSV: {len(df_csv_no_cruzados)}")
st.dataframe(df_csv_no_cruzados)

# Cruces desde la perspectiva del Excel
excel_perspective_cruces = []
for cruzado in registros_cruzados:
        registro_csv = cruzado.iloc[:len(df_csv.columns)]
        registro_excel = cruzado.iloc[len(df_csv.columns):]
        combined_record = pd.concat([registro_excel, registro_csv], axis=0)
        excel_perspective_cruces.append(combined_record)
df_excel_perspective_cruces = pd.DataFrame(excel_perspective_cruces)
st.write("Cruces desde la perspectiva del Excel:")
st.write(f"Cantidad de registros cruzados desde Excel: {len(df_excel_perspective_cruces)}")
st.dataframe(df_excel_perspective_cruces)
    # Registros sin cruzar en el Excel
df_excel_no_cruzados = df_excel[~df_excel['cruzado']].copy()
st.write("Registros del Excel sin cruzar:")
st.write(f"Cantidad de registros sin cruzar en Excel: {len(df_excel_no_cruzados)}")
st.dataframe(df_excel_no_cruzados)
    # Nuevo cruce con gastos bancarios
# Cruce adicional: gastos bancarios
descripciones_filtro = [
    "COMISION PAGO A OTROS BANCOS",
    "COBRO IVA PAGOS AUTOMATICOS",
    "IVA COMIS TRASL SUC VIRTUAL",
    "COMISION TRASL SUC VIRTUAL",
    "COMISION PAGO A PROVEEDORES",
    "COMISION PAGO DE NOMINA",
    "CUOTA MANEJO TARJETA PREPAGO",
    "IVA POR COMISIONES CORRIENTE",
    "CUOTA MANEJO SUC VIRT EMPRESA",
    "IVA CUOTA MANEJO SUC VIRT EMP"
]

df_csv_no_cruzados['Usado_en_cruce_gastos'] = False  # Añadir esta columna para marcar los registros
suma_salidas_filtro = 0

for idx, row in df_csv_no_cruzados.iterrows():
    if row['DESCRIPCION'] in descripciones_filtro:
        suma_salidas_filtro += row['Salidas']
        df_csv_no_cruzados.at[idx, 'Usado_en_cruce_gastos'] = True  # Marcar como usado sin sobrescribir el DataFrame


df_registros_usados_csv = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_gastos']]
st.write("Registros utilizados del CSV para la suma de gastos bancarios:")
st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_csv)}")
st.dataframe(df_registros_usados_csv)
st.write(f"Suma total de Salidas utilizadas: {suma_salidas_filtro}")

registro_gastos_bancarios = df_excel_no_cruzados[
    df_excel_no_cruzados['Observaciones'].str.contains("GASTOS BANCARIOS CUENTA", case=False, na=False) &
    (df_excel_no_cruzados['Credito'] > 0)
]

if not registro_gastos_bancarios.empty:
    registro_gastos = registro_gastos_bancarios.iloc[0]
    diferencia = registro_gastos['Credito'] - suma_salidas_filtro
    cruce_gastos = pd.concat([registro_gastos, df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_gastos']].sum(numeric_only=True)], axis=0)
    cruce_gastos['Diferencia'] = diferencia
    cruce_gastos['Nota'] = f"Cruce parcial con diferencia de {diferencia:.2f}. Registros CSV usados: {df_csv_no_cruzados['Usado_en_cruce_gastos'].sum()}"

    df_excel.at[registro_gastos.name, 'cruzado'] = True
    registros_cruzados.append(cruce_gastos)

    st.write("Resultado del cruce de gastos bancarios:")
    st.write("Registro del Excel con el que se cruzó:")
    st.dataframe(registro_gastos.to_frame().T)
    st.write(f"Diferencia entre la suma del CSV y el registro del Excel: {diferencia}")

    # Excluir los registros marcados del DataFrame final de no cruzados
    df_csv_no_cruzados = df_csv_no_cruzados[~df_csv_no_cruzados['Usado_en_cruce_gastos']]

  # Cruce adicional: servicios de telecomunicaciones
descripciones_servicios = [
    "PAGO PSE UNE - EPM Telecomuni",
    "PAGO SV TIGO SERVICIOS HOGAR"
]

df_csv_no_cruzados['Usado_en_cruce_servicios'] = False  # Añadir esta columna para marcar los registros
suma_servicios = 0

for idx, row in df_csv_no_cruzados.iterrows():
    if row['DESCRIPCION'] in descripciones_servicios:
        suma_servicios += row['Salidas']
        df_csv_no_cruzados.at[idx, 'Usado_en_cruce_servicios'] = True  # Marcar como usado sin sobrescribir el DataFrame


df_registros_usados_csv_servicios = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_servicios']]
st.write("Registros utilizados del CSV para el cruce de servicios:")
st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_csv_servicios)}")
st.dataframe(df_registros_usados_csv_servicios)
st.write(f"Suma total de Salidas utilizadas para servicios: {suma_servicios}")

registro_servicios_bancarios = df_excel_no_cruzados[
    df_excel_no_cruzados['Observaciones'].str.contains("SERVICIOS PUBLICOS INTERNET", case=False, na=False) &
    (df_excel_no_cruzados['Credito'] > 0)
]

if not registro_servicios_bancarios.empty:
    registro_servicios = registro_servicios_bancarios.iloc[0]
    diferencia_servicios = registro_servicios['Credito'] - suma_servicios
    cruce_servicios = pd.concat([registro_servicios, df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_servicios']].sum(numeric_only=True)], axis=0)
    cruce_servicios['Diferencia'] = diferencia_servicios
    cruce_servicios['Nota'] = f"Cruce parcial con diferencia de {diferencia_servicios:.2f}. Registros CSV usados: {df_csv_no_cruzados['Usado_en_cruce_servicios'].sum()}"

    df_excel.at[registro_servicios.name, 'cruzado'] = True
    registros_cruzados.append(cruce_servicios)

    st.write("Resultado del cruce de servicios:")
    st.write("Registro del Excel con el que se cruzó:")
    st.dataframe(registro_servicios.to_frame().T)
    st.write(f"Diferencia entre la suma del CSV y el registro del Excel: {diferencia_servicios}")

# Excluir todos los registros marcados en cruce de gastos y servicios de telecomunicaciones
df_csv_no_cruzados_final = df_csv_no_cruzados[
    ~df_csv_no_cruzados['Usado_en_cruce_gastos'] &
    ~df_csv_no_cruzados['Usado_en_cruce_servicios']
]

# Cruce manual aproximado de registros restantes (±1 peso)
st.subheader("Cruce Manual de Registros Restantes (±1 peso)")

df_csv_no_cruzados_final['Usado_en_cruce_aproximado'] = False  # Evita modificar el original
registros_confirmados = []

# Bucle para buscar registros manualmente entre los no cruzados en el CSV y Excel
for idx_csv, row_csv in df_csv_no_cruzados_final[df_csv_no_cruzados_final['Salidas'] > 0].iterrows():
    posibles_cruces = df_excel_no_cruzados[
        (df_excel_no_cruzados['Debito'] > 0) &
        (df_excel_no_cruzados['Debito'] >= row_csv['Salidas'] - 1) &
        (df_excel_no_cruzados['Debito'] <= row_csv['Salidas'] + 1)
    ]

    if not posibles_cruces.empty:
        st.write(f"Registro CSV:")
        st.write(row_csv[['FECHA', 'Salidas', 'DESCRIPCION']])
        
        for idx_excel, row_excel in posibles_cruces.iterrows():
            diferencia = row_excel['Debito'] - row_csv['Salidas']
            st.write("Posible cruce en Excel:")
            st.write(row_excel[['Fecha documento', 'Debito', 'Observaciones']])
            st.write(f"Diferencia: {diferencia:.2f}")

            # Botón de confirmación de cruce para el usuario
            if st.button(f"Confirmar cruce para registro CSV {idx_csv} y Excel {idx_excel}", key=f"confirm_{idx_csv}_{idx_excel}"):
                cruce_confirmado = pd.concat([row_csv, row_excel], axis=0)
                cruce_confirmado['Diferencia'] = diferencia
                registros_confirmados.append(cruce_confirmado)

                # Marcar los registros como cruzados
                df_csv_no_cruzados_final.at[idx_csv, 'Usado_en_cruce_aproximado'] = True
                df_excel.at[idx_excel, 'cruzado'] = True

# Actualizar DataFrames finales después de los cruces confirmados
df_cruzados = pd.concat([df_cruzados] + registros_confirmados, ignore_index=True)
df_csv_no_cruzados_final = df_csv_no_cruzados_final[~df_csv_no_cruzados_final['Usado_en_cruce_aproximado']]

# Mostrar los DataFrames actualizados
st.write("Registros cruzados (incluyendo cruces aproximados):")
st.write(f"Cantidad de registros cruzados (total): {len(df_cruzados)}")
st.dataframe(df_cruzados)

st.write("Registros no cruzados en el CSV (final):")
st.write(f"Cantidad de registros no cruzados en CSV (final): {len(df_csv_no_cruzados_final)}")
st.dataframe(df_csv_no_cruzados_final)

st.write("Registros del Excel sin cruzar (actualizado):")
st.write(f"Cantidad de registros sin cruzar en Excel (actualizado): {len(df_excel[~df_excel['cruzado']])}")
st.dataframe(df_excel[~df_excel['cruzado']])

# Visualización final de DataFrames
st.write("Registros cruzados (con cruce adicional de gastos y servicios):")
st.write(f"Cantidad de registros cruzados (total): {len(df_cruzados)}")
st.dataframe(df_cruzados)






    


