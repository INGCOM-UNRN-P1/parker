"""Cambios de ABI entre dos entregas de una librería (revisión 07, parker).

Una entrega que quita una función pública o le cambia la firma rompe a quien la usaba compilado
contra la versión anterior. `parker diff antes/ despues/` compara las declaraciones públicas de las
cabeceras y, si los dos lados traen binarios (.so/.o), los símbolos exportados.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from parker.core.abi_checker import descubrir_artefactos
from parker.core.models import AbiIssue, AbiReport
from parker.core.symbol_inspector import BinarioNoInspeccionable, inspect_elf_symbols, parse_header_declarations


_TIPOS = {"void", "char", "short", "int", "long", "float", "double", "signed", "unsigned", "const", "volatile",
          "struct", "union", "enum", "bool", "_Bool", "size_t"}


def _tipo_del_parametro(parametro: str) -> str:
    """El tipo de un parámetro sin su nombre: los nombres no son parte del ABI."""
    p = re.sub(r"\s*\*\s*", " * ", parametro).split()
    if len(p) >= 2 and re.fullmatch(r"[A-Za-z_]\w*", p[-1]) and p[-1] not in _TIPOS and not p[-1].endswith("_t"):
        p = p[:-1]
    return " ".join(p).replace(" * ", "*").replace(" *", "*")


def _normalizar(firma: str) -> str:
    firma = re.sub(r"\s+", " ", firma).strip()
    m = re.match(r"(.*?)\((.*)\)$", firma)
    if not m:
        return firma
    cabeza, params = m.group(1), m.group(2)
    tipos = [_tipo_del_parametro(x) for x in params.split(",")] if params.strip() else []
    return re.sub(r"\s*\*\s*", "*", cabeza.strip()) + "(" + ",".join(tipos) + ")"


def _publicas(raiz: Path) -> Dict[str, str]:
    cabeceras = [raiz] if raiz.is_file() else descubrir_artefactos(raiz)[0]
    publicas: Dict[str, str] = {}
    for h in cabeceras:
        for d in parse_header_declarations(h.read_text(encoding="utf-8", errors="replace")):
            if not d.is_static:
                publicas[d.name] = d.signature
    return publicas


def _exportados(raiz: Path) -> Dict[str, str]:
    if raiz.is_file():
        return {}
    exportados: Dict[str, str] = {}
    for b in descubrir_artefactos(raiz)[1]:
        try:
            for s in inspect_elf_symbols(b):
                if s.is_defined:
                    exportados[s.name] = b.name
        except BinarioNoInspeccionable:
            continue
    return exportados


def comparar(antes: Path, despues: Path) -> AbiReport:
    issues: List[AbiIssue] = []
    viejas, nuevas = _publicas(antes), _publicas(despues)
    for nombre, firma in sorted(viejas.items()):
        if nombre not in nuevas:
            issues.append(AbiIssue(code="PRK101", severity="ERROR", symbol_name=nombre, location=str(despues),
                                   message=f"Se quitó la función pública '{nombre}' ({firma}).",
                                   suggestion="Dejala (aunque sea como envoltorio de la nueva) o anunciá el cambio de versión mayor."))
        elif _normalizar(firma) != _normalizar(nuevas[nombre]):
            issues.append(AbiIssue(code="PRK102", severity="ERROR", symbol_name=nombre, location=str(despues),
                                   message=f"Cambió la firma de '{nombre}': {firma} → {nuevas[nombre]}.",
                                   suggestion="Un programa compilado con la firma anterior pasa mal los argumentos: agregá una función nueva en lugar de cambiar esta."))
    for nombre in sorted(set(nuevas) - set(viejas)):
        issues.append(AbiIssue(code="PRK103", severity="INFO", symbol_name=nombre, location=str(despues),
                               message=f"Función pública nueva: {nuevas[nombre]}.", suggestion="Agregar no rompe el ABI."))
    sim_viejos, sim_nuevos = _exportados(antes), _exportados(despues)
    if sim_viejos and sim_nuevos:
        for nombre in sorted(set(sim_viejos) - set(sim_nuevos) - set(viejas)):
            issues.append(AbiIssue(code="PRK104", severity="ERROR", symbol_name=nombre, location=sim_viejos[nombre],
                                   message=f"El binario ya no exporta '{nombre}'.",
                                   suggestion="Un programa enlazado contra la versión anterior no va a encontrar el símbolo."))
    return AbiReport(library_path=str(despues), header_path=str(antes), total_declarations_in_header=len(nuevas),
                     total_symbols_exported=len(sim_nuevos), issues=issues,
                     passed=not any(i.severity == "ERROR" for i in issues))
