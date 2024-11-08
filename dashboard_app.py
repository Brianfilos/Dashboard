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

    # Cruce directo desde CSV hacia Excel
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

    # Registros cruzados desde CSV hacia Excel
    df_cruzados_csv_to_excel = pd.DataFrame(registros_cruzados)
    st.write("Registros cruzados (desde CSV hacia Excel):")
    st.write(f"Cantidad de registros cruzados desde CSV: {len(df_cruzados_csv_to_excel)}")
    st.dataframe(df_cruzados_csv_to_excel)

    # Registros no cruzados en el CSV
    df_csv_no_cruzados = pd.DataFrame(registros_no_cruzados)
    st.write("Registros no cruzados en el CSV:")
    st.write(f"Cantidad de registros no cruzados en CSV: {len(df_csv_no_cruzados)}")
    st.dataframe(df_csv_no_cruzados)

    # Cruce desde la perspectiva del Excel hacia CSV
    registros_cruzados_excel_to_csv = []
    for idx_excel, row_excel in df_excel.iterrows():
        if not row_excel['cruzado']:  # Solo revisar registros no cruzados
            if row_excel['Debito'] > 0:
                cruce_entrada = df_csv[(df_csv['Entradas'] == row_excel['Debito'])]
                if not cruce_entrada.empty:
                    registro_csv = cruce_entrada.iloc[0]
                    registros_cruzados_excel_to_csv.append(pd.concat([row_excel, registro_csv], axis=0))
                    df_csv.at[registro_csv.name, 'cruzado'] = True
            elif row_excel['Credito'] > 0:
                cruce_salida = df_csv[(df_csv['Salidas'] == row_excel['Credito'])]
                if not cruce_salida.empty:
                    registro_csv = cruce_salida.iloc[0]
                    registros_cruzados_excel_to_csv.append(pd.concat([row_excel, registro_csv], axis=0))
                    df_csv.at[registro_csv.name, 'cruzado'] = True

    # Registros cruzados desde Excel hacia CSV
    df_cruzados_excel_to_csv = pd.DataFrame(registros_cruzados_excel_to_csv)
    st.write("Registros cruzados (desde Excel hacia CSV):")
    st.write(f"Cantidad de registros cruzados desde Excel: {len(df_cruzados_excel_to_csv)}")
    st.dataframe(df_cruzados_excel_to_csv)

    # Registros no cruzados en el Excel (desde perspectiva del Excel)
    df_excel_no_cruzados_final = df_excel[~df_excel['cruzado']]
    st.write("Registros del Excel sin cruzar (desde la perspectiva del Excel):")
    st.write(f"Cantidad de registros sin cruzar en Excel: {len(df_excel_no_cruzados_final)}")
    st.dataframe(df_excel_no_cruzados_final)










    


