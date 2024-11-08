import streamlit as st
import pandas as pd

st.title("Cargar y procesar archivo CSV y Excel")

# Cargar archivo CSV sin nombres de columna
csv_file = st.file_uploader("Cargar archivo CSV", type=["csv"])
if csv_file is not None:
    df_csv = pd.read_csv(csv_file, header=None, encoding='ISO-8859-1')
    column_names = ['CUENTA', 'SUCURSAL', 'Vacio', 'FECHA', 'Vacio2', 'VALOR', 'CODIGO', 'DESCRIPCION', 'ceros', 'extra']
    df_csv.columns = column_names[:df_csv.shape[1]]
    df_csv = df_csv.drop(columns=['Vacio', 'Vacio2', 'ceros', 'extra'], errors='ignore')
    df_csv['FECHA'] = pd.to_datetime(df_csv['FECHA'], format='%Y%m%d', errors='coerce')
    df_csv['Entradas'] = df_csv['VALOR'].apply(lambda x: x if x > 0 else 0)
    df_csv['Salidas'] = df_csv['VALOR'].apply(lambda x: -x if x < 0 else 0)
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
    df_excel['Debito'] = df_excel['Debito'].astype(float)
    df_excel['Credito'] = df_excel['Credito'].astype(float)
    registros_cruzados = []
    registros_no_cruzados = []
    df_excel['cruzado'] = False
    st.write("Datos del Excel cargado:")
    st.write(f"Total de registros en Excel: {df_excel.shape[0]}")
    st.dataframe(df_excel)

    # Primer cruce directo entre CSV y Excel
    for idx_csv, row_csv in df_csv.iterrows():
        if row_csv['Entradas'] > 0:
            cruce_entrada = df_excel[(df_excel['Debito'] == row_csv['Entradas']) & (~df_excel['cruzado'])]
            if not cruce_entrada.empty:
                registro_excel = cruce_entrada.iloc[0]
                registros_cruzados.append(pd.concat([row_csv, registro_excel], axis=0))
                df_excel.at[registro_excel.name, 'cruzado'] = True
            else:
                registros_no_cruzados.append(row_csv)
        elif row_csv['Salidas'] > 0:
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

    # Definir DataFrame de no cruzados si no existe después del cruce inicial
    if 'df_csv_no_cruzados' not in locals():
        df_csv_no_cruzados = pd.DataFrame(registros_no_cruzados)

    # Verifica que el DataFrame no esté vacío antes de añadir columnas adicionales
    if not df_csv_no_cruzados.empty:
        # Añadir columna para el cruce de gastos bancarios
        df_csv_no_cruzados['Usado_en_cruce_gastos'] = False

        # Realizar cruce con gastos bancarios
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
        suma_salidas_filtro = 0
        for idx, row in df_csv_no_cruzados.iterrows():
            if row['DESCRIPCION'].strip() in descripciones_filtro:
                suma_salidas_filtro += row['Salidas']
                df_csv_no_cruzados.at[idx, 'Usado_en_cruce_gastos'] = True
        df_registros_usados_csv = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_gastos']]
        st.write("Registros utilizados del CSV para la suma de gastos bancarios:")
        st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_csv)}")
        st.dataframe(df_registros_usados_csv)
        st.write(f"Suma total de Salidas utilizadas: {suma_salidas_filtro}")
        registro_gastos_bancarios = df_excel[~df_excel['cruzado'] & df_excel['Observaciones'].str.contains("GASTOS BANCARIOS CUENTA", case=False, na=False) & (df_excel['Credito'] > 0)]
        if not registro_gastos_bancarios.empty:
            registro_gastos = registro_gastos_bancarios.iloc[0]
            diferencia = registro_gastos['Credito'] - suma_salidas_filtro
            cruce_gastos = pd.concat([registro_gastos, df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_gastos']].sum(numeric_only=True)], axis=0)
            cruce_gastos['Diferencia'] = diferencia
            cruce_gastos['Nota'] = f"Cruce parcial con diferencia de {diferencia:.2f}"
            df_excel.at[registro_gastos.name, 'cruzado'] = True
            registros_cruzados.append(cruce_gastos)

        # Añadir columna para el cruce de servicios de telecomunicaciones
        df_csv_no_cruzados['Usado_en_cruce_servicios'] = False
        descripciones_servicios = ["PAGO PSE UNE - EPM Telecomuni", "PAGO SV TIGO SERVICIOS HOGAR"]
        suma_servicios = 0
        for idx, row in df_csv_no_cruzados.iterrows():
            if row['DESCRIPCION'].strip() in descripciones_servicios:
                suma_servicios += row['Salidas']
                df_csv_no_cruzados.at[idx, 'Usado_en_cruce_servicios'] = True
        df_registros_usados_csv_servicios = df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_servicios']]
        st.write("Registros utilizados del CSV para el cruce de servicios:")
        st.write(f"Cantidad de registros utilizados: {len(df_registros_usados_csv_servicios)}")
        st.dataframe(df_registros_usados_csv_servicios)
        st.write(f"Suma total de Salidas utilizadas para servicios: {suma_servicios}")
        registro_servicios_bancarios = df_excel[~df_excel['cruzado'] & df_excel['Observaciones'].str.contains("SERVICIOS PUBLICOS INTERNET", case=False, na=False) & (df_excel['Credito'] > 0)]
        if not registro_servicios_bancarios.empty:
            registro_servicios = registro_servicios_bancarios.iloc[0]
            diferencia_servicios = registro_servicios['Credito'] - suma_servicios
            cruce_servicios = pd.concat([registro_servicios, df_csv_no_cruzados[df_csv_no_cruzados['Usado_en_cruce_servicios']].sum(numeric_only=True)], axis=0)
            cruce_servicios['Diferencia'] = diferencia_servicios
            cruce_servicios['Nota'] = f"Cruce parcial con diferencia de {diferencia_servicios:.2f}"
            df_excel.at[registro_servicios.name, 'cruzado'] = True
            registros_cruzados.append(cruce_servicios)

        # Excluir registros cruzados de gastos y servicios
        df_csv_no_cruzados_final = df_csv_no_cruzados[~df_csv_no_cruzados['Usado_en_cruce_gastos'] & ~df_csv_no_cruzados['Usado_en_cruce_servicios']]

        # Cruce manual aproximado de registros restantes (±1 peso)
        st.subheader("Cruce Manual de Registros Restantes (±1 peso)")

        # Añadir columna para marcar registros usados en el cruce manual
        df_csv_no_cruzados_final['Usado_en_cruce_aproximado'] = False
        registros_confirmados = []
        
        for idx_csv, row_csv in df_csv_no_cruzados_final[df_csv_no_cruzados_final['Salidas'] > 0].iterrows():
            posibles_cruces = df_excel[~df_excel['cruzado'] & 
                                       (df_excel['Debito'] >= row_csv['Salidas'] - 1) & 
                                       (df_excel['Debito'] <= row_csv['Salidas'] + 1)]
            
            if not posibles_cruces.empty:
                st.write(f"Registro CSV:")
                st.write(row_csv[['FECHA', 'Salidas', 'DESCRIPCION']])
                
                for idx_excel, row_excel in posibles_cruces.iterrows():
                    diferencia = row_excel['Debito'] - row_csv['Salidas']
                    st.write("Posible cruce en Excel:")
                    st.write(row_excel[['Fecha documento', 'Debito', 'Observaciones']])
                    st.write(f"Diferencia: {diferencia:.2f}")
        
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






    


