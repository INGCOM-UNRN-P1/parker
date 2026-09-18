"""Verificación de coherencia y reglas de ABI en PARKER."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from parker.core.models import (
    AbiReport, AbiIssue, ExportedSymbol, HeaderDeclaration, SymbolVisibility
)
from parker.core.symbol_inspector import (
    BinarioNoInspeccionable,
    inspect_elf_symbols,
    parse_header_declarations,
)

_SUFIJOS_BINARIOS = (".so", ".o")


def descubrir_artefactos(raiz: Path) -> Tuple[List[Path], List[Path]]:
    """Cabeceras y binarios (.so/.o) de un proyecto, recursivamente.

    Se descartan los directorios ocultos (`.git`, `.venv`…): un `.venv` trae
    cientos de cabeceras y objetos ajenos al proyecto.
    """
    cabeceras: List[Path] = []
    binarios: List[Path] = []
    for directorio, subdirs, archivos in os.walk(raiz):
        subdirs[:] = sorted(d for d in subdirs if not d.startswith("."))
        for nombre in sorted(archivos):
            ruta = Path(directorio) / nombre
            if nombre.endswith(".h"):
                cabeceras.append(ruta)
            elif nombre.endswith(_SUFIJOS_BINARIOS):
                binarios.append(ruta)
    return cabeceras, binarios


def check_abi_compliance(
    header_path: Path,
    binary_path: Optional[Path] = None,
    allow_unexported_static: bool = True
) -> AbiReport:
    """Verifica correspondencia de símbolos, visibilidad y reglas de interfaz binaria."""
    binarios = [binary_path] if binary_path else []
    return auditar_abi([header_path], binarios)


def check_abi_project(raiz: Path, binarios: Optional[Sequence[Path]] = None) -> AbiReport:
    """Audita todas las cabeceras de un directorio contra la unión de sus binarios.

    Si se indican `binarios`, se usan en lugar de los que se descubran en el árbol.
    """
    cabeceras, encontrados = descubrir_artefactos(raiz)
    return auditar_abi(cabeceras, list(binarios) if binarios else encontrados, base=raiz, etiqueta=str(raiz))


def auditar_abi(
    cabeceras: Sequence[Path],
    binarios: Sequence[Path],
    base: Optional[Path] = None,
    etiqueta: Optional[str] = None,
) -> AbiReport:
    """Contrasta un conjunto de cabeceras con la unión de los símbolos de un conjunto de binarios.

    Una declaración solo falta si no está en NINGÚN binario, y un símbolo exportado
    solo es una fuga si no está declarado en NINGUNA cabecera: contrastar la
    cabecera contra `binarios[0]` acusaba de "no encontradas" las funciones que
    vivían en el segundo objeto.
    """
    def nombre(ruta: Path) -> str:
        if base is not None:
            try:
                return str(ruta.relative_to(base))
            except ValueError:
                pass
        return ruta.name

    issues: List[AbiIssue] = []
    declaraciones: Dict[Path, List[HeaderDeclaration]] = {}
    for cabecera in cabeceras:
        declaraciones[cabecera] = parse_header_declarations(cabecera.read_text(encoding="utf-8", errors="replace"))

    # 1. Chequeos sintácticos y de diseño en las cabeceras
    for cabecera, decls in declaraciones.items():
        for decl in decls:
            if decl.is_static:
                issues.append(AbiIssue(
                    code="PRK001",
                    severity="WARNING",
                    symbol_name=decl.name,
                    message=f"Función '{decl.name}' declarada como 'static' en cabecera pública.",
                    location=f"{nombre(cabecera)}:{decl.line_number}",
                    suggestion="Las funciones static en cabeceras se duplican en cada unidad de traducción. Declarala como 'static inline' o movela al archivo .c."
                ))

    # 2. Correspondencia con los binarios ELF, si se proveen
    binarios_existentes = [b for b in binarios if b.exists()]
    exportados: Dict[str, Tuple[ExportedSymbol, Path]] = {}
    total_exportados = 0
    hay_no_inspeccionados = False
    for binario in binarios_existentes:
        try:
            simbolos = inspect_elf_symbols(binario)
        except BinarioNoInspeccionable as exc:
            # Sin poder leer el binario NO se puede afirmar que falte ninguna
            # función: acusarlas a todas de "no encontradas" era un falso
            # positivo por cada declaración. Se informa una sola vez que la
            # verificación no se pudo hacer y se omite la comparación.
            hay_no_inspeccionados = True
            issues.append(AbiIssue(
                code="PRK000",
                severity="WARNING",
                symbol_name=binario.name,
                message=f"No se pudo verificar {binario.name} contra la cabecera: {exc}.",
                location=str(binario.name),
                suggestion="Comprobá que sea un binario ELF (.so/.o) válido y que binutils esté instalado (`parker doctor`).",
            ))
            continue
        total_exportados += len(simbolos)
        for simbolo in simbolos:
            exportados.setdefault(simbolo.name, (simbolo, binario))

    nombres_cabecera = {d.name for decls in declaraciones.values() for d in decls if not d.is_static}
    nombres_exportados = {
        n for n, (simbolo, _) in exportados.items() if simbolo.visibility == SymbolVisibility.DEFAULT
    }
    inspeccionados = len(binarios_existentes) - sum(1 for i in issues if i.code == "PRK000")

    if inspeccionados > 0:
        donde = (
            f"en {nombre(next(iter(declaraciones)))}" if len(declaraciones) == 1
            else f"en ninguna de las {len(declaraciones)} cabeceras auditadas"
        )
        # Símbolos exportados pero no documentados en las cabeceras (posible fuga de ABI)
        for simbolo_nombre, (simbolo, binario) in exportados.items():
            # Ignorar símbolos del compilador o runtime (empiezan con _)
            if simbolo_nombre.startswith("_") or simbolo_nombre in ("init", "fini", "main"):
                continue
            if simbolo_nombre not in nombres_cabecera and simbolo.visibility == SymbolVisibility.DEFAULT:
                issues.append(AbiIssue(
                    code="PRK002",
                    severity="WARNING",
                    symbol_name=simbolo_nombre,
                    message=f"Símbolo '{simbolo_nombre}' exportado globalmente pero no declarado {donde}.",
                    location=str(binario.name),
                    suggestion=f"Si es una función interna, agregá 'static' en el .c o '__attribute__((visibility(\"hidden\")))' para evitar contaminar la ABI pública."
                ))

        # Símbolos declarados en las cabeceras pero ausentes de los binarios. Con un
        # binario ilegible no se puede afirmar que falten: podrían estar ahí.
        if not hay_no_inspeccionados:
            etiqueta_binarios = (
                binarios_existentes[0].name if len(binarios_existentes) == 1
                else f"ninguno de los {len(binarios_existentes)} binarios"
            )
            for cabecera, decls in declaraciones.items():
                for decl in decls:
                    if not decl.is_static and decl.name not in nombres_exportados:
                        issues.append(AbiIssue(
                            code="PRK003",
                            severity="ERROR",
                            symbol_name=decl.name,
                            message=f"Función '{decl.name}' declarada en cabecera pero no encontrada en los símbolos exportados de {etiqueta_binarios}.",
                            location=f"{nombre(cabecera)}:{decl.line_number}",
                            suggestion=f"Asegurate de que '{decl.name}' esté implementada y no haya sido declarada como static en el código fuente."
                        ))

    # Determinar si aprobó (sin severidad ERROR)
    has_errors = any(i.severity == "ERROR" for i in issues)

    return AbiReport(
        library_path=", ".join(str(b) if base is None else nombre(b) for b in binarios_existentes) or None,
        header_path=etiqueta if etiqueta is not None else (str(cabeceras[0]) if len(cabeceras) == 1 else None),
        headers=[nombre(h) for h in cabeceras],
        binaries=[nombre(b) for b in binarios_existentes],
        total_symbols_exported=total_exportados,
        total_declarations_in_header=sum(len(d) for d in declaraciones.values()),
        issues=issues,
        passed=not has_errors
    )
