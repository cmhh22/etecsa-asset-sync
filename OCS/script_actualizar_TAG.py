import pandas as pd
import mysql.connector  # type: ignore
import sys
import logging
from pathlib import Path
from decouple import config
from openpyxl import load_workbook

# ---------------------------------------------------------------------------
# Configuration from .env
# ---------------------------------------------------------------------------
bd_nombre = config('DB_NAME', default='ocsweb')
usuario = config('DB_USER', default='root')
contrasena = config('DB_PASSWORD', default='')
host = config('DB_HOST', default='localhost')
puerto = config('DB_PORT', default=3306, cast=int)

nombre_tabla = config('TABLA_ACCOUNTINFO', default='accountinfo')
nombre_columna = config('COLUMNA_INVENTARIO', default='fields_3')

archivo_registro = config('ARCHIVO_REGISTRO', default='Registros.txt')

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(archivo_registro, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load Excel data sources
# ---------------------------------------------------------------------------
archivo_economia = config('EXCEL_ECONOMIA', default='AR01-1.xlsx')
skip_filas_economia = 8
columnas_economia = [5, 8]  # Columna 6 (No_inventario), columna 9 (Local)
df_economia = pd.read_excel(archivo_economia, skiprows=skip_filas_economia, usecols=columnas_economia)

archivo_clasificador = config('EXCEL_CLASIFICADOR', default='CLASIFICADOR DE LOCALES -KARINA-1.xlsx')
columnas_clasificador = [4, 5, 6]  # Columna 5 (ID_LOCAL), columna 6 (DESCRIP_LOCAL), columna 7 (EDIFICIO)
df_clasificador_locales = pd.read_excel(archivo_clasificador, usecols=columnas_clasificador)

# Función optimizada para buscar el número de inventario y devolver el valor del local
def buscar_inventario_y_local(numero_inventario):
    numero_inventario = numero_inventario.strip()  # Limpiar el número de inventario

    # Limpiar espacios en blanco de la columna de Noinventarios 
    inventario_economia_limpio = df_economia.iloc[:, 0].astype(str).str.strip()

    # Comprobar si el número de inventario está en la columna limpia
    if numero_inventario in inventario_economia_limpio.values:
        # Obtener el índice de la fila que coincide
        indice_fila = inventario_economia_limpio[inventario_economia_limpio == numero_inventario].index[0]
        local = df_economia.iloc[indice_fila, 1]  # Obtener el valor de la columna de local
        return local.strip() if isinstance(local, str) else local  # Limpiar si es cadena
    return None


# Función para buscar el local en el clasificador y devolver valores de columnas 6(DESCRIP_LOCAL) y 7(EDIFICIO)
def buscar_valores_en_clasificador(local):
    local = local.strip()
    fila = df_clasificador_locales[df_clasificador_locales.iloc[:, 0].astype(str).str.strip() == local]
    if not fila.empty:
        DESCRIP_LOCAL = str(fila.iloc[0, 1]).strip().replace(" ", "_")
        EDIFICIO = str(fila.iloc[0, 2]).strip().replace(" ", "_")
        return DESCRIP_LOCAL, EDIFICIO  # Devolver valores 
    return None

# Función principal para recorrer y procesar la columna 
def automatizar_y_procesar_datos(bd_nombre, usuario, contrasena, host, puerto, nombre_tabla, nombre_columna):
    try:
        logger.info('Iniciando sincronización de TAGs...')

        # Conectar a la base de datos MySQL
        connection = mysql.connector.connect(
            database=bd_nombre,
            user=usuario,
            password=contrasena,
            host=host,
            port=puerto
        )
        cursor = connection.cursor()

        # Ejecutar la consulta
        consulta = f'SELECT * FROM {nombre_tabla}'
        cursor.execute(consulta)
        filas_bd = cursor.fetchall()
        nombres_columnas = [desc[0] for desc in cursor.description]

        # Inicializar listas para diferentes condiciones
        inventarios_mv = []
        inventarios_vacios = []
        inventarios_duplicados = []
        inv_bd_no_estan_AR01 = []
        locales_no_estan_clasificador = []
        inventario_vistos = {} #Diccionario q almacena inventarios ya procesados ,se usa para detectar duplicados,
        inventarios_en_bd = []  #Almacena todos los inventarios de la BD, se usa para detectar inventarios del AR01 no están en la BD

        # Inventario en AR01 sin espacios ("limpios")
        inventarios_AR01_limpios = df_economia.iloc[:, 0].astype(str).str.strip().values

        for index, fila in enumerate(filas_bd, start=1):
            numero_inventario = fila[nombres_columnas.index(nombre_columna)]  
            valor_hadware_id = fila[nombres_columnas.index('HARDWARE_ID')]  

            logger.info(f"{index}. {numero_inventario}")

            if numero_inventario is None:
                inventarios_vacios.append(fila)
            elif numero_inventario == 'MV':
                inventarios_mv.append(fila)
            else:
                # Limpiamos el número de inventario
                numero_inventario = str(numero_inventario).strip()

                # Agregar el inventario en BD y en Vistos
                inventarios_en_bd.append(numero_inventario)
                inventario_vistos.setdefault(numero_inventario, []).append((fila, valor_hadware_id))
                
                # Verificar si el inventario no está en AR01
                if numero_inventario not in inventarios_AR01_limpios:
                    inv_bd_no_estan_AR01.append(fila)

                local_encontrado = buscar_inventario_y_local(numero_inventario)
                if local_encontrado:
                    valores = buscar_valores_en_clasificador(local_encontrado)
                    if valores:
                        descripcion_local, edificio = valores
                        resultado_valores = f"[ {edificio}-{descripcion_local} ]"
                        resultado_valores_bd = f"{edificio}-{descripcion_local}"

                        consulta_actualizacion = f'''
                            UPDATE {nombre_tabla} 
                            SET `TAG` = %s 
                            WHERE TRIM(`{nombre_columna}`) = %s
                        '''
                        cursor.execute(consulta_actualizacion, (resultado_valores_bd, numero_inventario))
                        connection.commit()
                        logger.info(f"TAG actualizado para inventario {numero_inventario} con valor {resultado_valores}")
                    else:
                        logger.warning(f"Local {local_encontrado} no encontrado en el clasificador para inventario {numero_inventario}")
                        locales_no_estan_clasificador.append((numero_inventario, local_encontrado))
                else:
                    logger.warning(f"No se encontró el inventario {numero_inventario} en el AR01")


        # Procesar duplicados 
        for _, valores in inventario_vistos.items():
            #Identificamos  duplicados
            if len(valores) > 1:
                # Ordenar por 'HARDWARE_ID' (mayor a menor)
                valores_ordenados = sorted(valores, key=lambda x: x[nombres_columnas.index('HARDWARE_ID')], reverse=True)

                for fila, _ in valores_ordenados:
                    # Actualizar el TAG antes de agregar a la lista de duplicados
                    numero_inventario = fila[nombres_columnas.index(nombre_columna)]
                    local_encontrado = buscar_inventario_y_local(str(numero_inventario).strip())
                    if local_encontrado:
                        resultado_valores = buscar_valores_en_clasificador(local_encontrado)
                        if resultado_valores:
                            fila_como_dict = dict(zip(nombres_columnas, fila))  # Convertir la fila a diccionario
                            fila_como_dict['TAG'] = f" {resultado_valores[1]}-{resultado_valores[0]} "  # Mantener corchetes en duplicados
                            # Se agregan los inventarios duplicados con su TAG actualizado 
                            inventarios_duplicados.append(fila_como_dict)

        # Comparar inventarios de AR01 con los que están en la base de datos
        inventarios_AR01_no_en_BD = [inv for inv in inventarios_AR01_limpios if inv not in inventarios_en_bd]

        # Locales correspondientes a inventarios no encontrados en la DB
        locales_correspondientes = [buscar_inventario_y_local(inv) for inv in inventarios_AR01_no_en_BD]

        # Generar DataFrames
        def generar_dataframe_con_mensaje(data, columnas, mensaje_encontrado, mensaje_no_encontrado):
            """
            Genera un DataFrame si la lista 'data' no está vacía. 
            Imprime el mensaje correspondiente si se encontraron o no elementos.
            """
            if data:
                df = pd.DataFrame(data, columns=columnas)
                logger.info(f"\n{mensaje_encontrado}")
                logger.info(f"\n{df}")
            else:
                df = pd.DataFrame(columns=columnas)
                logger.info(f"\n{mensaje_no_encontrado}")
            return df

        # Generar DataFrames optimizando la repetición
        df_duplicados = generar_dataframe_con_mensaje(
            inventarios_duplicados, 
            nombres_columnas, 
            "Filas con inventarios duplicados:", 
            "No se encontraron filas con inventarios duplicados."
        )

        df_vacios = generar_dataframe_con_mensaje(
            inventarios_vacios, 
            nombres_columnas, 
            "Filas con 'None':", 
            "No se encontraron filas con 'None'."
        )

        df_mv = generar_dataframe_con_mensaje(
            inventarios_mv, 
            nombres_columnas, 
            "Filas con 'MV':", 
            "No se encontraron filas con 'MV'."
        )

        df_inv_bd_no_estan_AR01 = generar_dataframe_con_mensaje(
            inv_bd_no_estan_AR01, 
            nombres_columnas, 
            "Inventarios de OCS no encontrados en AR01:", 
            "Todos los inventarios están en AR01."
        )

        # DataFrame con inventarios que están en AR01 pero no en la base de datos
        df_inv_AR01_no_estan_BD = pd.DataFrame({
            'Inventario en AR01 no en DB': inventarios_AR01_no_en_BD,
            'Local Correspondiente': locales_correspondientes
        })

        # DataFrame para locales no encontrados en el clasificador
        df_locales_no_estan_clasificador = generar_dataframe_con_mensaje(
            locales_no_estan_clasificador, 
            ['Inventario', 'Local'], 
            "Locales no encontrados en el clasificador:", 
            "Todos los locales están en el clasificador."
        )

        # Función para ajustar el ancho de las columnas
        def ajustar_ancho_columnas(writer):
            for hoja in writer.sheets.values():
                for columna in hoja.columns:
                    # Obtener la longitud máxima de las celdas no vacías en la columna
                    max_longitud = max(
                        (len(str(celda.value)) for celda in columna if celda.value), 
                        default=0
                    )
                    # Ajustar el ancho de la columna
                    ancho_ajustado = (max_longitud + 2) * 1.2
                    hoja.column_dimensions[columna[0].column_letter].width = ancho_ajustado  
                      
        # Guardar resultados en un archivo Excel
        hojas_y_dataframes = [
            ('Inventarios_Vacíos', df_vacios),
            ('Inventarios_MV', df_mv),
            ('Locales_no_están_Clasificador', df_locales_no_estan_clasificador),
            ('Inventarios_Duplicados', df_duplicados),
            ('Inv_BD_no_están_AR01', df_inv_bd_no_estan_AR01),
            ('Inv_AR01_no_están_DB', df_inv_AR01_no_estan_BD)
        ]

        with pd.ExcelWriter('Reportes.xlsx', engine='openpyxl') as writer:
            for nombre_hoja, df in hojas_y_dataframes:
                df.to_excel(writer, sheet_name=nombre_hoja, index=False)

             # Ajustar el ancho de las columnas
            ajustar_ancho_columnas(writer)

        logger.info("\nInforme generado con éxito: Reportes.xlsx")

    except mysql.connector.Error as err:
        logger.error(f"Error de base de datos: {err}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
        logger.info('Sincronización finalizada.')

# Llamar a la función principal
automatizar_y_procesar_datos(bd_nombre, usuario, contrasena, host, puerto, nombre_tabla, nombre_columna)

