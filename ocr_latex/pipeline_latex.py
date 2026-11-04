#!/usr/bin/env python3
"""
pipeline_latex.py — clasificador_selectividad
=============================================

Convierte PDFs de enunciados de selectividad (máx. 2 páginas cada uno)
en LaTeX usando la API de Anthropic, compila cada ejercicio con tectonic
y genera un PNG para revisarlo visualmente.

Flujo en dos fases (cada una en paralelo con hilos):
    Fase 1 · API:       PDF -> JSON con los ejercicios (o caché si ya existe)
    Fase 2 · Compilar:  ejercicio -> .tex standalone -> tectonic -> PDF -> PNG
Al final se vuelca todo a un CSV y se imprime un resumen OK/FALLO.

Cada .tex/.png lleva al pie una línea con: año. asignatura. convocatoria. tema. ejercicio

Uso:
    python pipeline_latex.py ./pdfs/integrales --limite 3
    python pipeline_latex.py ./pdfs/integrales --hilos 6
    python pipeline_latex.py ./pdfs/integrales --forzar          # ignora la caché
    python pipeline_latex.py ./pdfs/integrales --tema "Integrales"
    python pipeline_latex.py ./pdfs/integrales --modelo haiku    # -> salida_latex_haiku/

Salida (por defecto en salida_latex/):
    json/   caché de la API (<pdf>.json) + respuesta cruda (<pdf>.raw.txt)
    tex/    .tex, .pdf compilado y .log.txt si falla
    png/    imagen de cada ejercicio para comparar con el original
    enunciados_latex.csv

Especificación: PIPELINE_OCR_LATEX.md (fases 1-3: transcripción, validación
y consolidación; el cruce con ids y la clasificación van en otro script).

Requisitos:
    pip install anthropic pymupdf
    tectonic en el PATH
    ANTHROPIC_API_KEY en un .env (se busca hacia arriba hasta la raíz del repo)
"""

import argparse
import base64
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic   # SDK oficial de Anthropic
import pymupdf     # PyMuPDF (nombre moderno; antes "fitz"): leer PDFs y rasterizar a PNG

# Barra de progreso. Versión de texto de tqdm: funciona igual en terminal y en
# Jupyter sin necesitar ipywidgets (tqdm.auto/tqdm.notebook sí lo necesitan).
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------

# Modelos disponibles. Se eligen con --modelo haiku | sonnet
# (también vale pasar el id completo de cualquier otro modelo).
MODELO_HAIKU = "claude-haiku-5-5"     # más rápido y barato
MODELO_SONNET = "claude-sonnet-5-5"   # más fiable en matrices y fórmulas largas
MODELOS = {"haiku": MODELO_HAIKU, "sonnet": MODELO_SONNET}
MODELO_POR_DEFECTO = "sonnet"
MAX_PAGINAS = 5           # los PDFs de entrada solo deben tener enunciados
MAX_TOKENS = 8000         # margen de sobra para 8-10 ejercicios en LaTeX
DPI_PNG = 200             # resolución de los PNG de revisión
TIMEOUT_TECTONIC = 180    # segundos; la 1ª compilación descarga paquetes
HILOS_POR_DEFECTO = 4     # llamadas a la API / compilaciones simultáneas

COLUMNAS_CSV = ["archivo", "n", "anio", "asignatura", "convocatoria", "tema", "ejercicio",
                "cabecera", "latex", "compila", "png"]

# Instrucciones al modelo. Lo importante:
#  - La IMAGEN de la página es la fuente de verdad.
#  - Además del LaTeX, pedimos los metadatos ya separados (año, convocatoria,
#    ejercicio) para montar el pie y facilitar el cruce con los ids.
PROMPT_SISTEMA = r"""Eres un transcriptor experto de exámenes de matemáticas, física y química a LaTeX.

Recibirás un PDF con enunciados de selectividad. Reglas:

1. La IMAGEN de la página manda. El PDF puede traer una capa de texto incrustada
   con errores (símbolos mal codificados, matrices y fórmulas desordenadas,
   exponentes perdidos). Usa la capa de texto SOLO como ayuda para palabras y
   acentos; las fórmulas, matrices y números se transcriben de lo que SE VE.
2. Separa cada ejercicio. Para cada uno devuelve:
   - "cabecera": el encabezado del ejercicio copiado literalmente tal como aparece. Sin LaTeX.
   Los metadatos (asignatura, año, convocatoria, ejercicio) suelen estar en la
   cabecera o en el PIE de cada enunciado (p. ej. "MATEMÁTICAS II. 2026. RESERVA 4.
   EJERCICIO 2"). Búscalos en ambos sitios y sepáralos así:
   - "anio": año del examen, solo el número (p. ej. "2019"). "" si no aparece.
   - "asignatura": nombre de la asignatura tal como aparece, en mayúsculas y
     minúsculas normales (p. ej. "Matemáticas II", "Química"). "" si no aparece.
   - "convocatoria": tal como aparece (p. ej. "Junio", "Septiembre", "Reserva 1",
     "Ordinaria", "Extraordinaria"). "" si no aparece.
   - "ejercicio": identificador del ejercicio (opción/bloque y número, p. ej. "A3",
     "Ejercicio 2", "B1"). "" si no aparece.
   - "latex": SOLO el cuerpo del enunciado en LaTeX (texto + fórmulas).
     * Sin preámbulo, sin \documentclass, sin \begin{document}.
     * No repitas la cabecera dentro del LaTeX.
     * Matemáticas en línea con $...$; fórmulas destacadas con \[ ... \].
     * Convenciones obligatorias:
       - Integrales: \int_{a}^{b} f(x)\,dx  (con \, antes de dx)
       - Cocientes: \dfrac{...}{...}
       - Matrices: pmatrix.  Determinantes: vmatrix.
       - Sistemas de ecuaciones y funciones a trozos: cases.
     * Respeta los apartados a), b), c)..., cada uno en su propio párrafo,
       y conserva las puntuaciones tal como aparecen (p. ej. "(1.25 puntos)").
     * Si hay una figura o gráfica, no la dibujes: escribe \textit{[Figura: breve descripción]}.
     * No resuelvas nada: solo el enunciado.
3. Responde ÚNICAMENTE con JSON válido, sin texto antes ni después y sin ```:
   {"ejercicios": [{"cabecera": "...", "anio": "...", "asignatura": "...",
                    "convocatoria": "...",
                    "ejercicio": "...", "latex": "..."}]}
   Escapa cada barra invertida de LaTeX UNA sola vez dentro del JSON (\\frac, \\int,
   \\begin{cases}) y escribe los saltos de línea como \n (con una sola barra).
   No escapes dos veces: nada de \\\\frac ni \\n.
"""

PROMPT_USUARIO = "Transcribe todos los ejercicios de este PDF siguiendo las reglas."

# Plantilla standalone: varwidth hace que la página se ajuste al contenido.
# - fontspec: necesario con tectonic (motor XeTeX) para que salgan las tildes.
# - babel spanish con es-noshorthands: castellano sin atajos que rompan el LaTeX.
# Hay dos huecos: {cuerpo} (enunciado) y {pie} (línea de metadatos).
# Las llaves de LaTeX van dobladas {{ }} porque usamos str.format().
PLANTILLA_TEX = r"""\documentclass[varwidth=16cm,border=8pt]{{standalone}}
\usepackage{{fontspec}}
\usepackage[spanish,es-noshorthands]{{babel}}
\usepackage{{amsmath,amssymb}}
\setlength{{\parskip}}{{4pt}}
\begin{{document}}
{cuerpo}

\par\vspace{{6pt}}\noindent\rule{{\linewidth}}{{0.4pt}}\par\vspace{{2pt}}
\noindent{{\footnotesize\textit{{{pie}}}}}
\end{{document}}
"""


# ---------------------------------------------------------------------------
# Variables de entorno (.env)
# ---------------------------------------------------------------------------

def buscar_env(inicio: Path) -> Path | None:
    """Busca un .env en 'inicio' y en sus carpetas padre, hasta la raíz."""
    for carpeta in [inicio, *inicio.parents]:
        candidato = carpeta / ".env"
        if candidato.is_file():
            return candidato
    return None


def cargar_env(ruta: Path) -> None:
    """Lee un .env sencillo (CLAVE=valor) y lo pasa a os.environ.

    - Ignora líneas vacías y comentarios (#).
    - Quita comillas alrededor del valor.
    - setdefault NO pisa una variable que ya exista en la terminal.
    """
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)   # 1: corta solo en el primer '='
        clave = clave.removeprefix("export").strip()
        os.environ.setdefault(clave, valor.strip().strip('"').strip("'"))


def preparar_clave(ruta_env: Path | None) -> None:
    """Carga el .env y comprueba que existe ANTHROPIC_API_KEY."""
    ruta = ruta_env or buscar_env(Path.cwd()) \
        or buscar_env(Path(__file__).resolve().parent)
    if ruta:
        cargar_env(ruta)
        print(f".env cargado: {ruta.resolve()}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta ANTHROPIC_API_KEY (ponla en .env o expórtala en la terminal)")


# ---------------------------------------------------------------------------
# Utilidades de entrada
# ---------------------------------------------------------------------------

def listar_pdfs(carpeta: Path, limite: int | None) -> list[Path]:
    """PDFs de la carpeta (y subcarpetas, rglob es recursivo) ordenados."""
    pdfs = sorted(carpeta.rglob("*.pdf"))
    return pdfs[:limite] if limite else pdfs


def contar_paginas(ruta_pdf: Path) -> int:
    """Nº de páginas del PDF. 'with' garantiza que el archivo se cierra."""
    with pymupdf.open(ruta_pdf) as doc:
        return doc.page_count


def pdf_a_base64(ruta_pdf: Path) -> str:
    """Lee el PDF como bytes y lo codifica en base64 (texto) para la API."""
    return base64.standard_b64encode(ruta_pdf.read_bytes()).decode("utf-8")


def nombre_base(ruta_pdf: Path, carpeta: Path) -> str:
    """Nombre único y sin espacios para los archivos derivados.

    'Mates II_2026 - Integrales_enunciados.pdf' -> 'Mates_II_2026_Integrales_enunciados'
    """
    relativa = ruta_pdf.relative_to(carpeta).with_suffix("")
    return re.sub(r"[^\w]+", "_", "_".join(relativa.parts)).strip("_")


def tema_desde_nombre(ruta_pdf: Path) -> str:
    """Deduce el tema del nombre del PDF.

    Toma lo que hay tras el último ' - ' y quita el sufijo '_enunciados':
    'Mates II_2026 - Integrales_enunciados.pdf' -> 'Integrales'
    Si el nombre no sigue ese patrón, devuelve el nombre de la carpeta.
    """
    nombre = ruta_pdf.stem
    if " - " in nombre:
        tema = nombre.rsplit(" - ", 1)[1]
        tema = re.sub(r"[_ ]?enunciados?$", "", tema, flags=re.IGNORECASE)
        return tema.replace("_", " ").strip()
    return ruta_pdf.parent.name


# ---------------------------------------------------------------------------
# Fase 1 · Llamada a la API y caché
# ---------------------------------------------------------------------------

def llamar_api(cliente: anthropic.Anthropic, ruta_pdf: Path, modelo: str) -> str:
    """Envía el PDF como bloque 'document' y devuelve el texto de la respuesta."""
    respuesta = cliente.messages.create(
        model=modelo,
        max_tokens=MAX_TOKENS,
        system=PROMPT_SISTEMA,
        messages=[{
            "role": "user",
            "content": [
                {"type": "document",
                 "source": {"type": "base64", "media_type": "application/pdf",
                            "data": pdf_a_base64(ruta_pdf)}},
                {"type": "text", "text": PROMPT_USUARIO},
            ],
        }],
    )
    if respuesta.stop_reason == "max_tokens":
        raise RuntimeError("respuesta cortada por max_tokens; sube MAX_TOKENS")
    return "".join(b.text for b in respuesta.content if b.type == "text")


def extraer_json(texto: str) -> dict:
    """Convierte la respuesta del modelo en dict, tolerando ```json y texto extra."""
    limpio = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip())
    inicio, fin = limpio.find("{"), limpio.rfind("}")
    if inicio == -1 or fin == -1:
        raise ValueError("la respuesta no contiene JSON")
    datos = json.loads(limpio[inicio:fin + 1], strict=False)
    validar_estructura(datos)
    return datos


def reparar_latex(texto: str) -> str:
    """Deshace los errores de escape del modelo al meter LaTeX dentro de JSON.

    1. Barra sin escapar: json.loads convierte \\frac, \\begin, \\text, \\rightarrow
       en caracteres de control (\\f, \\b, \\t, \\r) + resto de la palabra.
       Se recuperan cuando van seguidos de una letra.
    2. Doble escape: si aparece \\\\begin, \\\\[ ... todo el texto viene
       con las barras dobladas y se dejan en una.
    3. Saltos de línea escritos como \\n literal -> salto real. Se respetan
       los comandos que empiezan por \\n (\\neq, \\nabla, \\not, \\noindent...).
    """
    control = {"\f": "f", "\b": "b", "\t": "t", "\r": "r"}
    texto = re.sub(r"([\f\b\t\r])(?=[A-Za-z])",
                   lambda m: "\\" + control[m.group(1)], texto)
    if re.search(r"\\\\[A-Za-z\[\]]", texto):
        texto = texto.replace("\\\\", "\\")
    texto = re.sub(r"\\n(?!eq|e\b|abla|ot|ewline|ewpage|oindent|u\b|i\b"
                   r"|leq|geq|mid|exists|subseteq|parallel)", "\n", texto)
    return texto


def validar_estructura(datos: dict) -> None:
    """Comprueba que el JSON tiene la forma {"ejercicios":[{cabecera, latex, ...}]}."""
    ejercicios = datos.get("ejercicios")
    if not isinstance(ejercicios, list) or not ejercicios:
        raise ValueError("falta la lista 'ejercicios' o está vacía")
    for i, ej in enumerate(ejercicios, start=1):
        if not isinstance(ej, dict) or "latex" not in ej or "cabecera" not in ej:
            raise ValueError(f"el ejercicio {i} no tiene 'cabecera' y 'latex'")


def obtener_ejercicios(cliente, ruta_pdf: Path, ruta_cache: Path,
                       modelo: str, forzar: bool) -> tuple[list[dict], bool]:
    """Devuelve (ejercicios, venia_de_cache). Usa la caché salvo --forzar."""
    if ruta_cache.exists() and not forzar:
        datos = json.loads(ruta_cache.read_text(encoding="utf-8"))
        return datos["ejercicios"], True

    texto = llamar_api(cliente, ruta_pdf, modelo)
    ruta_cache.with_suffix(".raw.txt").write_text(texto, encoding="utf-8")
    datos = extraer_json(texto)
    ruta_cache.write_text(json.dumps(datos, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return datos["ejercicios"], False


def transcribir_pdf(cliente, ruta_pdf: Path, carpeta: Path, dirs: dict,
                    args) -> list[dict]:
    """Fase 1 de un PDF: devuelve una fila (dict) por ejercicio, sin compilar.

    Se ejecuta dentro de un hilo; si lanza excepción la recoge main().
    """
    paginas = contar_paginas(ruta_pdf)
    if paginas > MAX_PAGINAS:
        raise ValueError(f"tiene {paginas} páginas (máx. {MAX_PAGINAS})")

    base = nombre_base(ruta_pdf, carpeta)
    tema = args.tema or tema_desde_nombre(ruta_pdf)
    ejercicios, _ = obtener_ejercicios(
        cliente, ruta_pdf, dirs["json"] / f"{base}.json", args.modelo, args.forzar)

    # .get(..., "") por si la caché es antigua y no trae los metadatos nuevos
    return [{"archivo": base, "n": n,
             "anio": str(ej.get("anio", "")).strip(),
             "asignatura": ej.get("asignatura", "").strip(),
             "convocatoria": ej.get("convocatoria", "").strip(),
             "tema": tema,
             "ejercicio": ej.get("ejercicio", "").strip(),
             "cabecera": ej["cabecera"].strip(),
             "latex": reparar_latex(ej["latex"]).strip(),
             "compila": False, "png": ""}
            for n, ej in enumerate(ejercicios, start=1)]


# ---------------------------------------------------------------------------
# Fase 2 · Compilación LaTeX y PNG
# ---------------------------------------------------------------------------

def escapar_latex(texto: str) -> str:
    """Escapa los caracteres especiales de LaTeX en texto normal (para el pie).

    Un '_' o '&' sueltos en la convocatoria romperían la compilación.
    """
    especiales = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                  "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                  "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(especiales.get(c, c) for c in texto)


def texto_pie(fila: dict) -> str:
    """Monta 'año. asignatura. convocatoria. tema. ejercicio' saltando los vacíos.

    Si el modelo no dio ningún metadato (p. ej. caché antigua), usa la cabecera.
    """
    if "Ejercicio" in fila["ejercicio"]:
        ejercicio = fila["ejercicio"].replace("Ejercicio", "ejercicio")
        convocatoria_string = f'{fila["convocatoria"]}, {ejercicio}'
    else:
        convocatoria_string = f'{fila["convocatoria"]}, ejercicio {fila["ejercicio"]}'

    partes = [fila["anio"], fila["asignatura"], fila["tema"].capitalize(), 
              convocatoria_string]
    
    if not (fila["anio"] or fila["convocatoria"] or fila["ejercicio"]):
        partes = [fila["cabecera"], fila["tema"]]
    return ". ".join(escapar_latex(p) for p in partes if p)


def compilar_tex(contenido: str, ruta_tex: Path) -> Path | None:
    """Escribe el .tex y lo compila con tectonic. Devuelve el PDF o None.

    subprocess.run lanza un proceso externo; mientras espera, el hilo libera
    el GIL de Python, por eso varias compilaciones en hilos sí van en paralelo.
    """
    ruta_tex.write_text(contenido, encoding="utf-8")
    try:
        proceso = subprocess.run(
            ["tectonic", "--outdir", str(ruta_tex.parent), str(ruta_tex)],
            capture_output=True, text=True, timeout=TIMEOUT_TECTONIC)
    except subprocess.TimeoutExpired:
        ruta_tex.with_suffix(".log.txt").write_text("timeout", encoding="utf-8")
        return None

    ruta_pdf = ruta_tex.with_suffix(".pdf")
    if proceso.returncode != 0 or not ruta_pdf.exists():
        ruta_tex.with_suffix(".log.txt").write_text(
            proceso.stdout + "\n" + proceso.stderr, encoding="utf-8")
        return None
    return ruta_pdf


def pdf_a_png(ruta_pdf: Path, ruta_png: Path) -> None:
    """Rasteriza la primera página del PDF compilado a PNG."""
    with pymupdf.open(ruta_pdf) as doc:
        doc[0].get_pixmap(dpi=DPI_PNG).save(ruta_png)


def compilar_fila(fila: dict, dirs: dict) -> dict:
    """Compila un ejercicio (con su pie) y actualiza 'compila' y 'png'."""
    nombre = f"{fila['archivo']}_{fila['n']:02d}"
    contenido = PLANTILLA_TEX.format(cuerpo=fila["latex"], pie=texto_pie(fila))
    ruta_pdf = compilar_tex(contenido, dirs["tex"] / f"{nombre}.tex")
    if ruta_pdf:
        ruta_png = dirs["png"] / f"{nombre}.png"
        pdf_a_png(ruta_pdf, ruta_png)
        fila["compila"], fila["png"] = True, str(ruta_png)
    return fila


def compilar_todas(filas: list[dict], dirs: dict, hilos: int) -> None:
    """Compila todos los ejercicios en paralelo.

    El primero se compila solo: así tectonic descarga los paquetes una vez
    y los demás hilos los encuentran ya en su caché (evita descargas simultáneas).
    """
    if not filas:
        return
    fallos = 0
    with tqdm(total=len(filas), desc="LaTeX", unit="ej") as barra:
        def avanzar(fila: dict) -> None:
            """Suma un paso a la barra y cuenta los que no compilan."""
            nonlocal fallos            # modifica la variable de la función de fuera
            fallos += not fila["compila"]
            barra.update(1)
            barra.set_postfix(no_compilan=fallos)

        avanzar(compilar_fila(filas[0], dirs))
        with ThreadPoolExecutor(max_workers=hilos) as pool:
            # pool.map entrega los resultados en orden según van terminando
            for fila in pool.map(lambda f: compilar_fila(f, dirs), filas[1:]):
                avanzar(fila)


# ---------------------------------------------------------------------------
# Salida y resumen
# ---------------------------------------------------------------------------

def preparar_directorios(salida: Path) -> dict:
    """Crea las subcarpetas de salida y devuelve sus rutas en un dict."""
    dirs = {nombre: salida / nombre for nombre in ("json", "tex", "png")}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def guardar_csv(filas: list[dict], ruta_csv: Path) -> None:
    """Vuelca las filas al CSV. utf-8-sig para que Excel lea bien las tildes."""
    with ruta_csv.open("w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS_CSV)
        escritor.writeheader()
        escritor.writerows(filas)


def imprimir_resumen(resultados: dict, filas: list[dict], ruta_csv: Path) -> None:
    """Muestra el estado de cada PDF y los totales."""
    print("\n" + "=" * 60 + "\nRESUMEN\n" + "=" * 60)
    for nombre in sorted(resultados):
        estado = resultados[nombre]
        print(f"  {'OK   ' if estado == 'OK' else 'FALLO'}  {nombre}"
              + ("" if estado == "OK" else f"  -> {estado}"))
    n_ok = sum(1 for e in resultados.values() if e == "OK")
    compilan = sum(f["compila"] for f in filas)
    print(f"\nPDFs: {n_ok} OK / {len(resultados) - n_ok} FALLO")
    print(f"Ejercicios: {len(filas)} total, {compilan} compilan, "
          f"{len(filas) - compilan} no compilan")
    print(f"CSV: {ruta_csv}")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def leer_argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PDFs de enunciados -> LaTeX + PNG + CSV")
    p.add_argument("carpeta", type=Path, help="carpeta con los PDFs")
    p.add_argument("--salida", type=Path, default=None,
                   help="carpeta de salida (por defecto: salida_latex con sonnet, "
                        "salida_latex_haiku con haiku)")
    p.add_argument("--limite", type=int, default=None,
                   help="procesar solo los N primeros PDFs (para pruebas)")
    p.add_argument("--modelo", default=MODELO_POR_DEFECTO,
                   help=f"{' | '.join(MODELOS)} o un id completo "
                        f"(por defecto: {MODELO_POR_DEFECTO})")
    p.add_argument("--hilos", type=int, default=HILOS_POR_DEFECTO,
                   help=f"tareas simultáneas (por defecto {HILOS_POR_DEFECTO})")
    p.add_argument("--tema", default=None,
                   help="tema para el pie (por defecto se deduce del nombre del PDF)")
    p.add_argument("--forzar", action="store_true",
                   help="ignorar la caché y volver a llamar a la API")
    p.add_argument("--env", type=Path, default=None,
                   help="ruta del .env (por defecto se busca hacia arriba)")
    args = p.parse_args()
    resolver_modelo(args)
    return args


def resolver_modelo(args: argparse.Namespace) -> None:
    """Traduce el alias del modelo a su id y elige la carpeta de salida.

    - 'haiku' -> MODELO_HAIKU, 'sonnet' -> MODELO_SONNET; un id completo se deja igual.
    - Cada modelo tiene su propia carpeta de salida (y por tanto su propia
      caché), para poder comparar sin que un modelo reutilice el JSON del otro.
    """
    alias = args.modelo.lower()
    args.modelo = MODELOS.get(alias, args.modelo)
    if args.salida is None:
        sufijo = "" if args.modelo == MODELO_SONNET else "_" + (
            alias if alias in MODELOS else re.sub(r"[^\w]+", "_", alias))
        args.salida = Path("salida_latex" + sufijo)


def transcribir_todos(cliente, pdfs: list[Path], dirs: dict, args):
    """Fase 1 en paralelo: un hilo por PDF (hasta --hilos a la vez).

    as_completed devuelve cada tarea según va terminando; future.result()
    relanza la excepción del hilo, que capturamos para no parar el lote.
    """
    filas, resultados = [], {}
    with ThreadPoolExecutor(max_workers=args.hilos) as pool, \
            tqdm(total=len(pdfs), desc="API", unit="pdf") as barra:
        tareas = {pool.submit(transcribir_pdf, cliente, pdf, args.carpeta,
                              dirs, args): pdf for pdf in pdfs}
        for futuro in as_completed(tareas):
            nombre = str(tareas[futuro].relative_to(args.carpeta))
            try:
                filas += futuro.result()
                resultados[nombre] = "OK"
            except Exception as e:  # un PDF roto no debe parar el lote
                resultados[nombre] = f"{type(e).__name__}: {e}"
                #tqdm.write(f"  ERROR {nombre}: {resultados[nombre]}")
            barra.update(1)   # avanza la barra al terminar cada PDF
            barra.set_postfix(fallos=sum(e != "OK" for e in resultados.values()))
    # Los hilos terminan en cualquier orden: reordenamos por archivo y nº
    filas.sort(key=lambda f: (f["archivo"], f["n"]))
    return filas, resultados


def ejecutar(carpeta, salida=None, limite=None, modelo=MODELO_POR_DEFECTO,
             hilos=HILOS_POR_DEFECTO, tema=None, forzar=False, env=None) -> list[dict]:
    """Ejecuta el pipeline completo. Pensada para llamarla desde un notebook.

    Mismos parámetros que en la terminal (--salida, --limite, ...), pero como
    argumentos normales. Devuelve la lista de filas (una por ejercicio), que
    se convierte directamente en DataFrame con pd.DataFrame(filas).

    Ejemplo:
        from pipeline_latex import ejecutar
        filas = ejecutar("pdfs/integrales", limite=3, modelo="haiku")
    """
    # Namespace imita el objeto que devuelve argparse, así el resto del
    # código (que usa args.modelo, args.forzar...) no cambia.
    args = argparse.Namespace(
        carpeta=Path(carpeta), salida=Path(salida) if salida else None,
        limite=limite, modelo=modelo, hilos=hilos, tema=tema,
        forzar=forzar, env=Path(env) if env else None)
    resolver_modelo(args)
    preparar_clave(args.env)

    # raise en vez de sys.exit: en Jupyter, sys.exit corta la celda con un
    # SystemExit poco claro; una excepción normal se ve y se puede capturar.
    if not args.carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta: {args.carpeta}")
    pdfs = listar_pdfs(args.carpeta, args.limite)
    if not pdfs:
        raise FileNotFoundError(f"No hay PDFs en {args.carpeta}")

    print(f"Modelo: {args.modelo}  ·  salida: {args.salida}")
    dirs = preparar_directorios(args.salida)
    # El cliente es seguro para usarlo desde varios hilos.
    # max_retries: reintenta solo ante errores de red o límites de uso (429).
    cliente = anthropic.Anthropic(max_retries=3)

    filas, resultados = transcribir_todos(cliente, pdfs, dirs, args)

    if shutil.which("tectonic"):
        compilar_todas(filas, dirs, args.hilos)
    else:
        print("AVISO: tectonic no está en el PATH; no se compilará ni habrá PNG.")

    ruta_csv = args.salida / "enunciados_latex.csv"
    guardar_csv(filas, ruta_csv)
    imprimir_resumen(resultados, filas, ruta_csv)
    return filas


def main() -> None:
    """Entrada desde la terminal: lee los argumentos y llama a ejecutar()."""
    a = leer_argumentos()
    try:
        ejecutar(a.carpeta, a.salida, a.limite, a.modelo, a.hilos,
                 a.tema, a.forzar, a.env)
    except (FileNotFoundError, RuntimeError) as e:
        sys.exit(str(e))


# Este bloque solo se ejecuta con "python pipeline_latex.py ...".
# Al hacer "import pipeline_latex" desde un notebook NO se ejecuta.
if __name__ == "__main__":
    main()
