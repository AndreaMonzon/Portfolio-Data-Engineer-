import glob
import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
from datetime import datetime
import time
import os
import warnings
import smtplib
import csv
import oracledb
from dotenv import load_dotenv


load_dotenv()

def crear_connection():
    try:
        oracledb.init_oracle_client(lib_dir=os.getenv('DB_LIB_DIR'))
        conn = oracledb.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            dsn=os.getenv('DB_DSN')
        )
        return conn
    except Exception as e:
        print(f" Error de conexion a oracle: {e}")
        return None





def cargar_a_oracle_sircar(ruta_archivo, tabla, conexion):
    cursor = conexion.cursor()

    with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
        next(archivo)  # Salteamos encabezado

        for linea in archivo:
            datos = linea.strip().split(';')

            # Transformar fechas (posiciones 7 y 11 en base a tus columnas)
            try:
                fecha_pago = datetime.strptime(datos[7], '%Y%m%d')
            except:
                fecha_pago = None

            try:
                fecha_acred = datetime.strptime(datos[11], '%Y%m%d')
            except:
                fecha_acred = None

            # Reemplazar los campos en la lista original
            datos[7] = fecha_pago
            datos[11] = fecha_acred

            # Convertir a tipos adecuados (opcional: limpieza de vacíos, numéricos, etc.)
            datos_final = []
            for i, valor in enumerate(datos):
                if i in [0, 1, 4, 5, 8, 9, 13]:  # columnas NUMBER
                    datos_final.append(int(valor) if valor.strip() else None)
                elif i in [7, 11]:  # FECHA_PAGO y FECHA_ACRED ya son datetime
                    datos_final.append(valor)
                else:
                    datos_final.append(valor.strip())

            # Ejecutar inserción
            cursor.execute(f"""
                INSERT INTO {tabla} (
                    COD_AREA, CUIT, RAZON_SOCIAL, NRO_INGRESO_BRUTO,
                    ANIO_RECA, MES_RECA, NRO_BOLETA, FECHA_PAGO, TIPO_PAGO,
                    SIGNO_IMPORTE, IMPORTE, FECHA_ACRED, TIPO_ADHESION, TRAMO_DDJJ
                ) VALUES (
                    :1, :2, :3, :4,
                    :5, :6, :7, :8, :9,
                    :10, :11, :12, :13, :14
                )
            """, datos_final)

    conexion.commit()
    cursor.close()

def cargar_a_oracle_sifere(ruta_archivo, tabla, conexion):
    cursor = conexion.cursor()

    with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
        lector = csv.reader(archivo, delimiter=';', quotechar='"')
        next(lector)  # Salta encabezado

        for datos in lector:
            # Validación mínima
            if len(datos) < 17:
                print(f"Línea con columnas incompletas: {datos}")
                continue

            # Limpieza de PERIODO y valores numéricos
            datos[4] = datos[4].split()[0] if datos[4].strip() else None
            for i in range(12, 17):
                datos[i] = datos[i].replace('.', '').replace(',', '.') if datos[i].strip() else None

            # Fechas
            try:
                fecha_acreditacion = datetime.strptime(datos[10].strip(), '%d/%m/%Y') if datos[10].strip() else None
            except:
                fecha_acreditacion = None
            try:
                fecha_pago = datetime.strptime(datos[11].strip(), '%d/%m/%Y') if datos[11].strip() else None
            except:
                fecha_pago = None

            try:
                datos_final = [
                    int(datos[0]) if datos[0].strip().isdigit() else None,       # CUIT
                    int(datos[1]) if datos[1].strip().isdigit() else None,       # NRO_INSCRIPCION
                    datos[2].strip(),                                            # SICOM
                    datos[3].strip(),                                            # RAZON_SOCIAL
                    datos[4].strip(),                                            # PERIODO
                    int(datos[5]) if datos[5].strip().isdigit() else None,       # JUR
                    int(datos[6]) if datos[6].strip().isdigit() else None,       # FORM
                    int(datos[7]) if datos[7].strip().isdigit() else None,       # IMPUESTO
                    datos[8].strip(),                                            # BANCO
                    int(datos[9]) if datos[9].strip().isdigit() else None,       # NRO_TRANS_AFIP
                    fecha_acreditacion,
                    fecha_pago,
                    float(datos[12]) if datos[12] else None,
                    float(datos[13]) if datos[13] else None,
                    float(datos[14]) if datos[14] else None,
                    float(datos[15]) if datos[15] else None,
                    float(datos[16]) if datos[16] else None
                ]
            except Exception as e:
                print(f" Error procesando línea: {datos}")
                print(f"  Error: {e}")
                continue

            try:
                cursor.execute(f"""
                    INSERT INTO {tabla} (
                        CUIT, NRO_INSCRIPCION, SICOM, RAZON_SOCIAL, PERIODO,
                        JUR, FORM, IMPUESTO, BANCO, NRO_TRANS_AFIP,
                        FECHA_ACREDITACION, FECHA_PAGO, CREDITO_BRUTO,
                        COMISIONES, IVA, INTERESES, CREDITO_NETO
                    ) VALUES (
                        :1, :2, :3, :4, :5,
                        :6, :7, :8, :9, :10,
                        :11, :12, :13, :14, :15,
                        :16, :17
                    )
                """, datos_final)
            except Exception as e:
                print(f"Error al insertar en Oracle: {e}")
                print(f"Datos: {datos_final}")
                continue

    conexion.commit()
    cursor.close()
    print("Carga finalizada correctamente.")



def cargar_a_oracle_sircreb(ruta_archivo, tabla, conexion):

    cursor = conexion.cursor()

    with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
        next(archivo)  # Saltea la línea de encabezado
        lector = csv.reader(archivo, delimiter=',', quotechar='"')

        
        for fila in lector:
            if len(fila) != 13:
                print(f"Línea incompleta: {fila}")
                continue

            try:
                # Formatear fecha desde AAAAMMDD
                fecha_raw = fila[5].strip()
                fecha_pago = datetime.strptime(fecha_raw, "%Y%m%d") if fecha_raw else None

                datos = [
                    int(fila[0]),                        # COD_AREA
                    int(fila[1]),                        # CUIT_AGENTE
                    int(fila[2]),                        # ANIO
                    int(fila[3]),                        # MES
                    int(fila[4]),                        # DECENA_MES
                    fecha_pago,                          # FECHA_PAGO
                    fila[6].strip(),                     # OBLIGACION_FISCAL
                    int(fila[7]),                        # RECTIFICATIVA
                    str(int(fila[8])),                   # IMPORTE_INTERES (sin ceros a la izquierda)
                    int(fila[9]),                        # SIGNO_INTERES
                    str(int(fila[10])),                  # IMPORTE_RECAUDACIONES
                    int(fila[11]),                       # SIGNO_RECA
                    str(int(fila[12]))                   # IMPORTE_TOTAL
                ]

                cursor.execute(f"""
                    INSERT INTO {tabla} (
                        COD_AREA, CUIT_AGENTE, ANIO, MES, DECENA_MES,
                        FECHA_PAGO, OBLIGACION_FISCAL, RECTIFICATIVA,
                        IMPORTE_INTERES, SIGNO_INTERES,
                        IMPORTE_RECAUDACIONES, SIGNO_RECA, IMPORTE_TOTAL
                    ) VALUES (
                        :1, :2, :3, :4, :5,
                        :6, :7, :8, :9, :10,
                        :11, :12, :13
                    )
                """, datos)

            except Exception as e:
                print(f"Error procesando línea: {fila}")
                print(f"Error: {e}")
                continue

    conexion.commit()
    cursor.close()
    print("Carga finalizada correctamente.")



def limpiar_txt():
    txt_files = glob.glob("*.txt")
    txt_files = [f for f in txt_files if 'RecaudDetalle' not in f]
    for i in txt_files:
        os.remove(i)

     

##Definicion de la lista de archivos
os.chdir(os.getcwd())
my_files = glob.glob('*.zip')
print('------------LIST_OF_FILES-------------')
print(my_files)
print('--------------------------------------')


def tratar_sircreb():
#SIRCREB

    sircreb = [s for s in my_files if "_sircreb_" in s]
    print (sircreb)


    for i in sircreb:
        print (i)
        with zipfile.ZipFile(i, 'r') as zip_ref:
            zip_ref.extractall('')

    #PAGOS
            
        listOfFiles = ['pagos.txt']
        listOfData = []
        correct_data=[]
        first_characters = i[0: 3]

        for t in listOfFiles:

            with open (t,'r') as reader: 
                for line in reader.readlines()[:-1]:
                    listOfData.append(line)
                for i in listOfData:
                    correct_data.append( first_characters + ',' +
                    i[:11] + ',' + i[11:15] + ',' +
                    i[15:17] + ',' + i[17:18] + ',' +
                    i[18:26] + ',' + i[26:64] + ',' +
                    i[64:66] + ',' + i[66:84] + ',' +
                    i[84:85] + ',' + i[85:103]+ ',' +
                    i[103:104] + ',' + i[104:]  )
                listOfData = [] 

        with open ('SIRCREB_PAGOS_CORREGIDO_'+first_characters+'.txt','w') as f:
            for i in correct_data:
                f.write(i)

    with open("SIRCREB_ENCABEZADO_PAGOS.txt","w+") as f:
        f.write ('COD_AREA,CUIT,ANIO,MES,DECENA_MES,FECHA_PAGO,OBLIGACION_FISCAL,RECTIFICATIVA,IMPORTE_INTERES,SIGNO_INTERES,IMPORTE_RECAUDACIONES,SIGNO_RECA,IMPORTE_TOTAL\n')

    with open('SIRCREB_PAGOS_CORREGIDOS_TOT.txt', 'w') as end_file:
       for file_name in ['SIRCREB_ENCABEZADO_PAGOS.txt','SIRCREB_PAGOS_CORREGIDO_901.txt','SIRCREB_PAGOS_CORREGIDO_904.txt','SIRCREB_PAGOS_CORREGIDO_905.txt','SIRCREB_PAGOS_CORREGIDO_906.txt','SIRCREB_PAGOS_CORREGIDO_908.txt','SIRCREB_PAGOS_CORREGIDO_916.txt']:
            with open(file_name, 'r') as data_entry:
                content = data_entry.read()
                end_file.write(content)

    shutil.move(os.getcwd() + '/SIRCREB_PAGOS_CORREGIDOS_TOT.txt', os.getcwd() +'\Resultado/SIRCREB_PAGOS_CORREGIDOS_TOT.txt')

    limpiar_txt()
    conexion = crear_connection()
    cargar_a_oracle_sircreb('Resultado/SIRCREB_PAGOS_CORREGIDOS_TOT.txt', 'pagos_sircreb', conexion)



def tratar_sircar():
##SIRCAR

    sircar = [s for s in my_files if "_sircar_" in s]
    print (sircar)


    for i in sircar:
        print (i)
        with zipfile.ZipFile(i, 'r') as zip_ref:
            zip_ref.extractall('')

    #ACREDITACIONES

        listOfFiles = ['acreditaciones.txt']
        listOfData = []
        correct_data=[]
        first_characters = i[0: 3]


        for t in listOfFiles:

            with open (t,'r') as reader: 
                for line in reader.readlines():
                    listOfData.append(line)
                for i in listOfData:
                    correct_data.append( first_characters + ';' +
                    i[:11] + ';' + i[11:81] + ';' +
                    i[81:91] + ';' + i[91:95] + ';' +
                    i[95:97] + ';' + i[97:109] + ';' +
                    i[109:117] + ';' + i[117:120] + ';' +
                    i[120:121] + ';' + i[121:139]+ ';' +
                    i[139:147] + ';' + i[147:148] + ';' + i[148:]  )
                listOfData = [] 

        #correct_data.insert(0, 'COD_AREA;CUIT;RAZON_SOCIAL;NRO_INGRESO_BRUTO;ANIO_RECA;MES_RECA;NRO_BOLETA;FECHA_PAGO;TIPO_PAGO;SIGNO_IMPORTE;IMPORTE;FECHA_ACRED;TIPO_ADHESION;TRAMO_DDJJ\n')


        with open ('SIRCAR_ACREDITACIONES_CORREGIDO_'+first_characters+'.txt','w') as f:
            for i in correct_data:
                f.write(i)

    with open("SIRCAR_ENCABEZADO_ACREDITACIONES.txt","w+") as f:
            f.write ('COD_AREA;CUIT;RAZON_SOCIAL;NRO_INGRESO_BRUTO;ANIO_RECA;MES_RECA;NRO_BOLETA;FECHA_PAGO;TIPO_PAGO;SIGNO_IMPORTE;IMPORTE;FECHA_ACRED;TIPO_ADHESION;TRAMO_DDJJ\n')

    with open('SIRCAR_ACREDITACIONES_CORREGIDOS_TOT.txt', 'w') as end_file:
         for file_name in ['SIRCAR_ENCABEZADO_ACREDITACIONES.txt','SIRCAR_ACREDITACIONES_CORREGIDO_904.txt','SIRCAR_ACREDITACIONES_CORREGIDO_905.txt','SIRCAR_ACREDITACIONES_CORREGIDO_906.txt','SIRCAR_ACREDITACIONES_CORREGIDO_908.txt']:
              
        #for file_name in ['SIRCAR_ENCABEZADO_ACREDITACIONES.txt','SIRCAR_ACREDITACIONES_CORREGIDO_904.txt']:
            with open(file_name, 'r') as data_entry:
                content = data_entry.read()
                end_file.write(content)

    shutil.move(os.getcwd() + '/SIRCAR_ACREDITACIONES_CORREGIDOS_TOT.txt', os.getcwd() +'\Resultado/SIRCAR_ACREDITACIONES_CORREGIDOS_TOT.txt')
   

    limpiar_txt()
    conexion = crear_connection()
    cargar_a_oracle_sircar('Resultado/SIRCAR_ACREDITACIONES_CORREGIDOS_TOT.txt', 'ACREDITACIONES_SIRCAR', conexion)
 

def tratar_sifere():

    ##SIFERE

        #ACREDITACIONES

    txt_files = glob.glob('*.txt')
    print(txt_files)
    listOfData = []
    correct_data=[]


    for t in txt_files:
        first_characters = t[30: 33]
        with open (t,'r') as reader: 
            for line in reader.readlines()[2:]:
                listOfData.append(line)
            for i in listOfData:
                correct_data.append( 
                i[0:]  )
            listOfData = []


    #correct_data.insert(0, 'CUIT;Nro_Inscripcion;Sicom;Razon_Social;Periodo;Jur;Form;Impuesto;Banco;Nro_Trans_Afip;Fecha_Acreditacion;Fecha_Pago;Credito_Bruto;Comisiones;IVA;Intereses;Credito_Neto\n')


        with open ('SIFERE_ACREDITACIONES_CORREGIDO_'+first_characters+'.txt','w') as f:
            for i in correct_data:
                temp = i.replace('"', '')
                temp = i.replace('.', '')
                f.write(temp)
        correct_data = []

    with open("SIFERE_ENCABEZADO_ACREDITACIONES.txt","w+") as f:
            f.write ('CUIT;Nro_Inscripcion;Sicom;Razon_Social;Periodo;Jur;Form;Impuesto;Banco;Nro_Trans_Afip;Fecha_Acreditacion;Fecha_Pago;Credito_Bruto;Comisiones;IVA;Intereses;Credito_Neto\n')

    with open('SIFERE_ACREDITACIONES_CORREGIDOS_TOT.txt', 'w') as end_file:
        for file_name in ['SIFERE_ENCABEZADO_ACREDITACIONES.txt','SIFERE_ACREDITACIONES_CORREGIDO_901.txt','SIFERE_ACREDITACIONES_CORREGIDO_904.txt','SIFERE_ACREDITACIONES_CORREGIDO_905.txt','SIFERE_ACREDITACIONES_CORREGIDO_906.txt','SIFERE_ACREDITACIONES_CORREGIDO_908.txt']:
            
       # for file_name in ['SIFERE_ENCABEZADO_ACREDITACIONES.txt','SIFERE_ACREDITACIONES_CORREGIDO_908.txt']:
            with open(file_name, 'r') as data_entry:
                content = data_entry.read()
                end_file.write(content)

    shutil.move(os.getcwd() + '/SIFERE_ACREDITACIONES_CORREGIDOS_TOT.txt', os.getcwd() +'\Resultado/SIFERE_ACREDITACIONES_CORREGIDOS_TOT.txt')
    
    limpiar_txt()
    conexion = crear_connection()
    cargar_a_oracle_sifere('Resultado/SIFERE_ACREDITACIONES_CORREGIDOS_TOT.txt', 'ACREDITACIONES_SIFERE', conexion)
    conexion.close()



#PROCESO

print ('░░░░░░░░░░░░░ 0%')
tratar_sircar()
print('SIRCAR HA SIDO TRATADO CORRECTAMENTE')
print ('███░░░░░░░░░ 25%')
tratar_sifere()
print('SIFERE HA SIDO TRATADO CORRECTAMENTE')
print ('████████░░░░ 68%')
tratar_sircreb()
print('SIRCREB HA SIDO TRATADO CORRECTAMENTE')
print('██████████ 100%	')

