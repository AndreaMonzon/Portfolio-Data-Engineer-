import os
import shutil

# Definimos las carpetas principales y sus subcarpetas a procesar
config = {
    "SIFERE": ["901", "904", "905", "906", "908"],
    "SIRCAR": ["904", "905", "906", "908"],
    "SIRCREB": ["901", "904", "905", "906", "908", "916"]
}

# Carpeta raíz general (donde están SIFERE, SIRCAR, SIRCREB)
raiz = r"F:\Tableau\Regimenes CM"

# Carpeta destino fija
destino = r"C:\automatizacion\sircar-sircreb-sifere"
os.makedirs(destino, exist_ok=True)

for sistema, subcarpetas in config.items():
    for sub in subcarpetas:
        carpeta = os.path.join(raiz, sistema, sub)

        if not os.path.exists(carpeta):
            print(f"La carpeta {carpeta} no existe, se salta.")
            continue

        # Listar archivos en la subcarpeta
        archivos = [
            os.path.join(carpeta, f)
            for f in os.listdir(carpeta)
            if os.path.isfile(os.path.join(carpeta, f))
        ]

        if archivos:
            # Buscar el más reciente
            archivo_reciente = max(archivos, key=os.path.getmtime)

            # Usar el nombre original del archivo
            nombre_archivo = os.path.basename(archivo_reciente)
            destino_final = os.path.join(destino, nombre_archivo)

            # Copiar
            shutil.copy2(archivo_reciente, destino_final)

            print(f" {sistema} {sub} → '{nombre_archivo}' copiado a {destino_final}")
        else:
            print(f"⚠ No hay archivos en la carpeta {carpeta}")
