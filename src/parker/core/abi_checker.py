"""Verificación de coherencia y reglas de ABI en PARKER."""

from pathlib import Path
from typing import List, Optional
from parker.core.models import (
    AbiReport, AbiIssue, ExportedSymbol, HeaderDeclaration, SymbolVisibility
)
from parker.core.symbol_inspector import inspect_elf_symbols, parse_header_declarations


def check_abi_compliance(
    header_path: Path,
    binary_path: Optional[Path] = None,
    allow_unexported_static: bool = True
) -> AbiReport:
    """Verifica correspondencia de símbolos, visibilidad y reglas de interfaz binaria."""
    issues: List[AbiIssue] = []

    header_content = header_path.read_text(encoding="utf-8", errors="replace")
    declarations = parse_header_declarations(header_content)

    # 1. Chequeos sintácticos y de diseño en la cabecera
    for decl in declarations:
        if decl.is_static:
            issues.append(AbiIssue(
                code="PRK001",
                severity="WARNING",
                symbol_name=decl.name,
                message=f"Función '{decl.name}' declarada como 'static' en cabecera pública.",
                location=f"{header_path.name}:{decl.line_number}",
                suggestion="Las funciones static en cabeceras se duplican en cada unidad de traducción. Declarala como 'static inline' o movela al archivo .c."
            ))

    # 2. Chequeo de correspondencia con binario ELF si se provee
    exported_symbols: List[ExportedSymbol] = []
    if binary_path and binary_path.exists():
        exported_symbols = inspect_elf_symbols(binary_path)
        exported_names = {s.name for s in exported_symbols if s.visibility == SymbolVisibility.DEFAULT}
        header_names = {d.name for d in declarations if not d.is_static}

        # Símbolos exportados pero no documentados en la cabecera (posible fuga de ABI)
        for sym in exported_symbols:
            # Ignorar símbolos del compilador o runtime (empiezan con _)
            if sym.name.startswith("_") or sym.name in ("init", "fini", "main"):
                continue
            if sym.name not in header_names and sym.visibility == SymbolVisibility.DEFAULT:
                issues.append(AbiIssue(
                    code="PRK002",
                    severity="WARNING",
                    symbol_name=sym.name,
                    message=f"Símbolo '{sym.name}' exportado globalmente pero no declarado en {header_path.name}.",
                    location=str(binary_path.name),
                    suggestion=f"Si es una función interna, agregá 'static' en el .c o '__attribute__((visibility(\"hidden\")))' para evitar contaminar la ABI pública."
                ))

        # Símbolos declarados en la cabecera pero no encontrados en el binario
        for decl in declarations:
            if not decl.is_static and decl.name not in exported_names:
                issues.append(AbiIssue(
                    code="PRK003",
                    severity="ERROR",
                    symbol_name=decl.name,
                    message=f"Función '{decl.name}' declarada en cabecera pero no encontrada en los símbolos exportados de {binary_path.name}.",
                    location=f"{header_path.name}:{decl.line_number}",
                    suggestion=f"Asegurate de que '{decl.name}' esté implementada y no haya sido declarada como static en el código fuente."
                ))

    # Determinar si aprobó (sin severidad ERROR)
    has_errors = any(i.severity == "ERROR" for i in issues)

    return AbiReport(
        library_path=str(binary_path) if binary_path else None,
        header_path=str(header_path),
        total_symbols_exported=len(exported_symbols),
        total_declarations_in_header=len(declarations),
        issues=issues,
        passed=not has_errors
    )
