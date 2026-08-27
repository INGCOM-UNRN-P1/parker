"""Plugin de PARKER para el microkernel RIPLEY."""

from pathlib import Path
from typing import Dict, Any, List
from parker.core.abi_checker import check_abi_compliance


class ParkerPlugin:
    """Plugin de auditoría de ABI para Ripley."""

    name = "abi_audit"
    description = "Auditoría de interfaces binarias, símbolos exportados y cabeceras C"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        source_dir = Path(context.get("source_dir", "."))
        headers = list(source_dir.glob("*.h"))
        binaries = list(source_dir.glob("*.so")) + list(source_dir.glob("*.o"))

        issues_found = []
        all_passed = True

        for h in headers:
            bin_target = binaries[0] if binaries else None
            report = check_abi_compliance(h, bin_target)
            if not report.passed:
                all_passed = False
            for issue in report.issues:
                issues_found.append({
                    "code": issue.code,
                    "severity": issue.severity,
                    "symbol": issue.symbol_name,
                    "message": issue.message,
                    "location": issue.location,
                    "suggestion": issue.suggestion
                })

        return {
            "passed": all_passed,
            "issues_count": len(issues_found),
            "issues": issues_found
        }
