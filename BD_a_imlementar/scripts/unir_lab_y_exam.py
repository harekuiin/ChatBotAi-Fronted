import pandas as pd
from pathlib import Path
import re

# Carpeta donde están todos los archivos .XPT
data_folder = Path("data")
archivos = list(data_folder.glob("*.XPT")) + list(data_folder.glob("*.xpt"))

# Ciclos NHANES por letra
ciclos = {
    "E": "2007_2008",
    "F": "2009_2010",
    "G": "2011_2012"
}

# Inicializar agrupadores
lab_por_ciclo = {ciclo: [] for ciclo in ciclos.values()}
exam_por_ciclo = {ciclo: [] for ciclo in ciclos.values()}

# Clasificar archivos por tipo y ciclo
for archivo in archivos:
    nombre = archivo.stem.upper()
    match = re.search(r"_([EFG])", nombre)
    if match:
        letra = match.group(1)
        ciclo = ciclos[letra]
        if nombre.startswith(("ALB", "APO", "BIO", "CBC", "GHB", "GLU", "HDL", "OGTT", "TCHOL", "TRIGLY", "CRP")):
            lab_por_ciclo[ciclo].append(archivo)
        elif nombre.startswith(("BMX", "BPX", "ENX", "EXAM")):
            exam_por_ciclo[ciclo].append(archivo)
# Hay algunos archivos que tienen columnas del mismo tipo de dato generando errores, por lo tanto elimina la duplicada
# Función para unir archivos sin duplicar columnas
def unir_y_guardar(lista_archivos, tipo, ciclo):
    dfs = []
    for archivo in lista_archivos:
        try:
            df = pd.read_sas(archivo, format='xport', encoding='utf-8')
            dfs.append(df)
        except Exception as e:
            print(f"⚠️ Error al leer {archivo.name}: {e}")

    if not dfs:
        print(f"❌ No se encontraron archivos válidos para {tipo} {ciclo}")
        return

    df_final = dfs[0]
    for df in dfs[1:]:
        columnas_duplicadas = [col for col in df.columns if col in df_final.columns and col != "SEQN"]
        df = df.drop(columns=columnas_duplicadas)
        df_final = pd.merge(df_final, df, on="SEQN", how="outer")

    output_name = f"{tipo}_{ciclo}.csv"
    df_final.to_csv(output_name, index=False)
    print(f"✅ Guardado: {output_name}")

#Genera los archivos csv separado por años
# Ejecutar para LAB y EXAM
for ciclo in ciclos.values():
    unir_y_guardar(lab_por_ciclo[ciclo], "lab", ciclo)
    unir_y_guardar(exam_por_ciclo[ciclo], "exam", ciclo)
