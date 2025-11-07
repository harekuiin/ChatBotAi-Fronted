import pandas as pd
from pathlib import Path
import numpy as np

# Ciclos disponibles
ciclos = ["2007_2008", "2009_2010", "2011_2012"]

# Carpeta donde están los CSV ya convertidos
carpeta = Path("data")

for ciclo in ciclos:
    archivos = {
        "lab": carpeta / f"LAB_{ciclo}.csv",
        "exam": carpeta / f"EXAM{ciclo}.csv",
        "demo": carpeta / f"DEMO_{ciclo}.csv"
    }

    dfs = []
    for tipo, archivo in archivos.items():
        if archivo.exists():
            try:
                df = pd.read_csv(archivo)
                dfs.append(df)
            except Exception as e:
                print(f"⚠️ Error al leer {archivo.name}: {e}")
        else:
            print(f"❌ Archivo no encontrado: {archivo.name}")

    if dfs:
        df_final = dfs[0]
        for df in dfs[1:]:
            columnas_duplicadas = [col for col in df.columns if col in df_final.columns and col != "SEQN"]
            df = df.drop(columns=columnas_duplicadas)
            df_final = pd.merge(df_final, df, on="SEQN", how="outer")

        output_name = f"datos_completos_{ciclo}.csv"
        df_final.to_csv(output_name, index=False)
        print(f"✅ Guardado: {output_name}")
    else:
        print(f"❌ No se pudo unir datos para el ciclo {ciclo}")
missing_codes = [7, 9, 77, 99, 777, 999, 7777, 9999, '.', '']
for col in df.select_dtypes(include=[np.number]).columns:
    df[col] = df[col].replace(missing_codes, np.nan)
df = df.dropna()
