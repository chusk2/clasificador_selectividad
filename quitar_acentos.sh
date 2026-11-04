#!/usr/bin/env bash
# quitar_acentos.sh — Renombra carpetas y archivos quitando tildes y diacríticos.
#
# Funciona con tildes compuestas (NFC, Linux) y descompuestas (NFD, macOS).
# Por defecto solo SIMULA: muestra lo que haría sin tocar nada.
#
# Uso:
#   ./quitar_acentos.sh /ruta/a/carpeta            # simulación
#   ./quitar_acentos.sh /ruta/a/carpeta --aplicar  # renombra de verdad
#
# Nota: también convierte ñ -> n y ü -> u (igual que remove_accents en Python).

set -euo pipefail

RAIZ="${1:-}"
MODO="${2:-}"

if [[ -z "$RAIZ" || ! -d "$RAIZ" ]]; then
    echo "Uso: $0 <carpeta> [--aplicar]" >&2
    exit 1
fi

APLICAR=0
[[ "$MODO" == "--aplicar" ]] && APLICAR=1

command -v python3 >/dev/null || { echo "Hace falta python3" >&2; exit 1; }

sin_acentos() {
    python3 -c '
import sys, unicodedata
s = unicodedata.normalize("NFD", sys.argv[1])
print(unicodedata.normalize("NFC", "".join(c for c in s if unicodedata.category(c) != "Mn")), end="")
' "$1"
}

renombrados=0
conflictos=0

# -depth: primero el contenido y luego la carpeta, para que las rutas sigan siendo válidas
while IFS= read -r -d '' ruta; do
    dir="$(dirname -- "$ruta")"
    nombre="$(basename -- "$ruta")"
    nuevo="$(sin_acentos "$nombre")"

    [[ "$nombre" == "$nuevo" ]] && continue

    destino="$dir/$nuevo"
    if [[ -e "$destino" ]]; then
        echo "CONFLICTO (no se toca): '$ruta' -> ya existe '$destino'" >&2
        conflictos=$((conflictos + 1))
        continue
    fi

    echo "'$ruta'  ->  '$nuevo'"
    if (( APLICAR )); then
        mv -n -- "$ruta" "$destino"
    fi
    renombrados=$((renombrados + 1))
done < <(find "$RAIZ" -mindepth 1 -depth -print0)

echo
if (( APLICAR )); then
    echo "Renombrados: $renombrados | Conflictos: $conflictos"
else
    echo "SIMULACIÓN — se renombrarían: $renombrados | Conflictos: $conflictos"
    echo "Ejecuta de nuevo con --aplicar para hacerlo de verdad."
fi
