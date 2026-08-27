"""Renderizado Rich de reportes de auditoría ABI en PARKER."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from parker.core.models import AbiReport

console = Console()


def print_abi_report(report: AbiReport) -> None:
    """Imprime el reporte en la terminal utilizando tablas y paneles Rich."""
    if not report.issues:
        console.print(Panel(
            f"[bold green]✓ ABI Válida y Coherente[/bold green]\n"
            f"• Cabecera: {report.header_path}\n"
            f"• Declaraciones analizadas: {report.total_declarations_in_header}\n"
            f"• Símbolos exportados en binario: {report.total_symbols_exported}",
            title="[bold green]PARKER ABI Audit[/bold green]"
        ))
        return

    table = Table(title="Auditoría de Interfaz Binaria y Símbolos (ABI)", show_header=True, header_style="bold magenta")
    table.add_column("Código", style="cyan", width=8)
    table.add_column("Sev", style="bold", width=8)
    table.add_column("Símbolo", style="yellow")
    table.add_column("Ubicación", style="blue")
    table.add_column("Diagnóstico y Sugerencia", style="white")

    for issue in report.issues:
        sev_color = "red" if issue.severity == "ERROR" else "yellow"
        table.add_row(
            issue.code,
            f"[{sev_color}]{issue.severity}[/{sev_color}]",
            issue.symbol_name,
            issue.location,
            f"{issue.message}\n[dim]↳ Sugerencia: {issue.suggestion}[/dim]"
        )

    console.print(table)
    if report.passed:
        console.print("\n[bold yellow]⚠️ Se detectaron advertencias en la ABI, pero no hay discrepancias críticas.[/bold yellow]")
    else:
        console.print("\n[bold red]❌ Se detectaron fallos críticos de ABI que romperán el enlazado o la compatibilidad.[/bold red]")
