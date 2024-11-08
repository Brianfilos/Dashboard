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

    # Registros no cruzados en el CSV
    df_csv_no_cruzados = pd.DataFrame(registros_no_cruzados)
    st.write("Registros no cruzados en el CSV:")
    st.write(f"Cantidad de registros no cruzados en CSV: {len(df_csv_no_cruzados)}")
    st.dataframe(df_csv_no_cruzados)

    # Cruce adicional de gastos bancarios
    descripciones_gastos = [
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
    
    # Eliminar espacios adicionales en DESCRIPCION para asegurar la búsqueda correcta
    df_csv_no_cruzados['DESCRIPCION'] = df_csv_no_cruzados['DESCRIPCION'].str.strip()
    df_csv_no_cruzados['Usado_en_cruce_gastos'] = False
    suma_salidas_gastos = 0

    for idx, row in df_csv_no_cruzados.iterrows():
        if row['DESCRIPCION'] in descripciones_gastos:
            suma_salidas_gastos += row['Salidas']
            df_csv_no_cruzados.at[idx, 'Usado_en_cruce_gastos'] = True
    
    df_registros_usados_csv_gastos = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_gastos']]
    st.write("Registros utilizados del CSV para la suma de gastos bancarios:")
    st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_csv_gastos)}")
    st.dataframe(df_registros_usados_csv_gastos)
    st.write(f"Suma total de Salidas utilizadas: {suma_salidas_gastos}")

    # Buscar un registro en los no cruzados del Excel que contenga "GASTOS BANCARIOS CUENTA" en Observaciones
    registro_gastos_bancarios = df_excel[
        df_excel['Observaciones'].str.contains("GASTOS BANCARIOS CUENTA", case=False, na=False) & 
        (df_excel['Credito'] > 0)
    ]

    if not registro_gastos_bancarios.empty:
        registro_gastos = registro_gastos_bancarios.iloc[0]
        diferencia_gastos = registro_gastos['Credito'] - suma_salidas_gastos
        cruce_gastos = pd.concat([registro_gastos, df_registros_usados_csv_gastos.sum(numeric_only=True)], axis=0)
        cruce_gastos['Diferencia'] = diferencia_gastos
        cruce_gastos['Nota'] = f"Cruce parcial con diferencia de {diferencia_gastos:.2f}. Registros CSV usados: {df_csv_no_cruzados['Usado_en_cruce_gastos'].sum()}"
        df_excel.at[registro_gastos.name, 'cruzado'] = True
        registros_cruzados.append(cruce_gastos)

    # Cruce adicional: servicios de telecomunicaciones
    descripciones_servicios = [
        "PAGO PSE UNE - EPM Telecomuni",
        "PAGO SV TIGO SERVICIOS HOGAR"
    ]

    df_csv_no_cruzados['Usado_en_cruce_servicios'] = False
    suma_servicios = 0
    for idx, row in df_csv_no_cruzados.iterrows():
        if row['DESCRIPCION'] in descripciones_servicios:
            suma_servicios += row['Salidas']
            df_csv_no_cruzados.at[idx, 'Usado_en_cruce_servicios'] = True

    df_registros_usados_csv_servicios = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_servicios']]
    st.write("Registros utilizados del CSV para el cruce de servicios:")
    st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_csv_servicios)}")
    st.dataframe(df_registros_usados_csv_servicios)
    st.write(f"Suma total de Salidas utilizadas para servicios: {suma_servicios}")

    # Buscar registro en el Excel para servicios de telecomunicaciones
    registro_servicios_bancarios = df_excel[
        df_excel['Observaciones'].str.contains("SERVICIOS PUBLICOS INTERNET", case=False, na=False) & 
        (df_excel['Credito'] > 0)
    ]

    if not registro_servicios_bancarios.empty:
        registro_servicios = registro_servicios_bancarios.iloc[0]
        diferencia_servicios = registro_servicios['Credito'] - suma_servicios
        cruce_servicios = pd.concat([registro_servicios, df_registros_usados_csv_servicios.sum(numeric_only=True)], axis=0)
        cruce_servicios['Diferencia'] = diferencia_servicios
        cruce_servicios['Nota'] = f"Cruce parcial con diferencia de {diferencia_servicios:.2f}. Registros CSV usados: {df_csv_no_cruzados['Usado_en_cruce_servicios'].sum()}"
        df_excel.at[registro_servicios.name, 'cruzado'] = True
        registros_cruzados.append(cruce_servicios)

    # Excluir los registros cruzados de los DataFrames finales de no cruzados
    df_csv_no_cruzados_final = df_csv_no_cruzados[
        ~df_csv_no_cruzados['Usado_en_cruce_gastos'] &
        ~df_csv_no_cruzados['Usado_en_cruce_servicios']
    ].drop(columns=['Usado_en_cruce_gastos', 'Usado_en_cruce_servicios'])

    df_excel_no_cruzados_final = df_excel[~df_excel['cruzado']]

    # Mostrar los DataFrames finales
    st.write("Registros cruzados (con cruces adicionales):")
    st.write(f"Cantidad de registros cruzados (total): {len(registros_cruzados)}")
    st.dataframe(pd.DataFrame(registros_cruzados))

    st.write("Registros no cruzados en el CSV (final):")
    st.write(f"Cantidad de registros no cruzados en CSV (final): {len(df_csv_no_cruzados_final)}")
    st.dataframe(df_csv_no_cruzados_final)
    
    st.write("Registros del Excel sin cruzar (final):")
    st.write(f"Cantidad de registros sin cruzar en Excel (final): {len(df_excel_no_cruzados_final)}")
    st.dataframe(df_excel_no_cruzados_final)









    


