"""Inspección de símbolos en binarios ELF (.so, .o) y cabeceras .h."""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from parker.core.models import ExportedSymbol, SymbolType, SymbolVisibility, HeaderDeclaration


def parse_header_declarations(header_content: str) -> List[HeaderDeclaration]:
    """Extrae declaraciones de funciones públicas desde una cabecera C."""
    declarations = []
    # Limpiar comentarios
    clean = re.sub(r'/\*.*?\*/', '', header_content, flags=re.DOTALL)
    clean = re.sub(r'//.*', '', clean)

    # Patrón para funciones: tipo nombre(params);
    pattern = re.compile(
        r'^\s*(?:__attribute__\s*\(\(.*?\)\)\s*)?'
        r'(?:extern\s+)?'
        r'([a-zA-Z0-9_* ]+?)\s+'
        r'([a-zA-Z_][a-zA-Z0-9_]*)\s*'
        r'\(([^)]*)\)\s*;',
        re.MULTILINE
    )

    lines = header_content.splitlines()
    for match in pattern.finditer(clean):
        ret_type = match.group(1).strip()
        fn_name = match.group(2).strip()
        params = match.group(3).strip()
        full_sig = f"{ret_type} {fn_name}({params})"

        if fn_name in ('typedef', 'struct', 'union', 'enum', 'return', 'if', 'while'):
            continue

        # Encontrar línea aproximada
        line_no = 1
        for idx, line in enumerate(lines, 1):
            if fn_name in line:
                line_no = idx
                break

        has_visibility = "__attribute__" in match.group(0) or "visibility" in match.group(0)
        is_static = "static" in ret_type

        declarations.append(HeaderDeclaration(
            name=fn_name,
            return_type=ret_type,
            signature=full_sig,
            line_number=line_no,
            is_static=is_static,
            has_visibility_attribute=has_visibility
        ))

    return declarations


class BinarioNoInspeccionable(Exception):
    """No se pudieron leer los símbolos del binario (nm ausente o formato inválido).

    Es distinto de "el binario no exporta nada": confundirlos hacía que un
    archivo que no es ELF, o un `nm` que falla, se leyera como 0 símbolos y
    PRK003 acusara de "no implementada" a cada función de la cabecera.
    """


def inspect_elf_symbols(binary_path: Path) -> List[ExportedSymbol]:
    """Extrae símbolos de un binario (.so / .o) utilizando nm.

    Lanza `BinarioNoInspeccionable` si no se puede leer; devuelve una lista vacía
    solo cuando el binario es válido y de verdad no exporta símbolos.
    """
    symbols = []
    try:
        res = subprocess.run(
            ["nm", "-D", "--defined-only", str(binary_path)],
            capture_output=True,
            text=True,
            check=False
        )
        output = res.stdout
        if not output.strip() or res.returncode != 0:
            # Intentar nm sin -D (para archivos .o estáticos)
            res2 = subprocess.run(
                ["nm", "-g", "--defined-only", str(binary_path)],
                capture_output=True,
                text=True,
                check=False
            )
            output = res2.stdout
            if res.returncode != 0 and res2.returncode != 0:
                detalle = (res2.stderr or res.stderr or "").strip().splitlines()
                raise BinarioNoInspeccionable(
                    detalle[-1] if detalle else "nm no pudo leer el archivo"
                )

        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) >= 3:
                _addr, sym_type, name = parts[0], parts[1], parts[2]
                st = SymbolType.FUNCTION if sym_type in ('T', 't', 'W', 'w') else SymbolType.VARIABLE
                symbols.append(ExportedSymbol(
                    name=name,
                    symbol_type=st,
                    visibility=SymbolVisibility.DEFAULT if sym_type.isupper() else SymbolVisibility.HIDDEN,
                    is_defined=True
                ))
            elif len(parts) == 2:
                sym_type, name = parts[0], parts[1]
                st = SymbolType.FUNCTION if sym_type in ('T', 't', 'W', 'w') else SymbolType.VARIABLE
                symbols.append(ExportedSymbol(
                    name=name,
                    symbol_type=st,
                    visibility=SymbolVisibility.DEFAULT if sym_type.isupper() else SymbolVisibility.HIDDEN,
                    is_defined=True
                ))
    except FileNotFoundError:
        raise BinarioNoInspeccionable("la herramienta 'nm' (binutils) no está instalada")

    return symbols
