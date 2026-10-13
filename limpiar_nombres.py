from pathlib import Path

import pandas as pd

# Sin unicodedata.normalize: cubrimos tanto la forma Linux (á = 1 carácter)
# como la forma macOS (á = "a" + tilde suelta), borrando las tildes sueltas.
REEMPLAZOS = {
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
    "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
    "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
    "ü": "u", "Ü": "U", "ñ": "n", "Ñ": "N", "ç": "c", "Ç": "C",
    # Tildes sueltas (nombres que vienen del Mac): se borran y queda la letra base
    "́": "",  # ´ aguda
    "̀": "",  # ` grave
    "̂": "",  # ^ circunfleja
    "̃": "",  # ~ de la ñ
    "̈": "",  # ¨ diéresis
    "̧": "",  # ¸ cedilla
}


def sin_acentos(texto: str) -> str:
    for con, sin in REEMPLAZOS.items():
        texto = texto.replace(con, sin)
    if not texto.isascii():
        raise ValueError(f"Carácter no contemplado en: {texto!r}")
    return texto


def limpiar_nombre(nombre: str) -> str:
    """Quita acentos y espacios al principio y al final de un nombre de archivo o carpeta."""
    return sin_acentos(nombre).strip()


def limpiar_ruta(ruta):
    """Aplica limpiar_nombre a cada componente de una ruta (para las columnas del CSV)."""
    if pd.isna(ruta):
        return ruta
    partes = Path(ruta).parts
    return Path(*(limpiar_nombre(p) for p in partes)).as_posix()


def renombrar_archivos(raiz, simular=True):
    """Renombra archivos y carpetas bajo `raiz` quitando acentos.

    Con simular=True solo muestra los cambios. Devuelve la lista de (origen, destino).
    Recorre de abajo arriba para renombrar el contenido antes que su carpeta.
    """
    rutas = sorted(Path(raiz).rglob("*"), key=lambda p: len(p.parts), reverse=True)
    cambios, conflictos, destinos = [], [], set()

    for ruta in rutas:
        nuevo = limpiar_nombre(ruta.name)
        if nuevo == ruta.name:
            continue
        destino = ruta.with_name(nuevo)
        if destino.exists() or destino in destinos:
            conflictos.append((ruta, destino))
            continue
        destinos.add(destino)
        cambios.append((ruta, destino))

    for origen, destino in conflictos:
        print(f"CONFLICTO: {origen}  ->  {destino} (ya existe)")
    print(f"{len(cambios)} cambios, {len(conflictos)} conflictos en {raiz}")

    if not simular:
        if conflictos:
            raise RuntimeError("Hay conflictos: resuélvelos antes de renombrar")
        for origen, destino in cambios:
            origen.rename(destino)
    return cambios


def limpiar_csv(df, columnas=("archivo", "imagen")):
    """Devuelve una copia del DataFrame con las rutas de `columnas` limpias."""
    df = df.copy()
    for col in columnas:
        df[col] = df[col].map(limpiar_ruta)
    return df


def rutas_que_faltan(df, raiz=".", columnas=("archivo", "imagen")):
    """Rutas del DataFrame que no existen en disco (debería ser una lista vacía)."""
    raiz = Path(raiz)
    return [r for col in columnas for r in df[col].dropna() if not (raiz / r).exists()]
