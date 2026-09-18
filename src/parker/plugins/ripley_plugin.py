"""Plugin de PARKER para el microkernel RIPLEY."""

from pathlib import Path
from typing import Dict, Any
from parker.core.abi_checker import check_abi_project


class ParkerPlugin:
    """Plugin de auditoría de ABI para Ripley."""

    name = "abi_audit"
    description = "Auditoría de interfaces binarias, símbolos exportados y cabeceras C"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        source_dir = Path(context.get("source_dir", "."))
        # Todas las cabeceras contra la unión de todos los binarios del árbol: contrastar
        # contra el primero que devolviera el glob acusaba de faltantes a las funciones
        # implementadas en los demás, y el glob no recursivo perdía los subdirectorios.
        report = check_abi_project(source_dir)

        issues_found = [
            {
                "code": issue.code,
                "severity": issue.severity,
                "symbol": issue.symbol_name,
                "message": issue.message,
                "location": issue.location,
                "suggestion": issue.suggestion,
            }
            for issue in report.issues
        ]
        return {
            "passed": report.passed,
            "issues_count": len(issues_found),
            "issues": issues_found,
        }
