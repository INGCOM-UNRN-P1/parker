"""Tests unitarios y de integración para PARKER."""

from pathlib import Path
from typer.testing import CliRunner
from parker.cli import app
from parker.core.abi_checker import check_abi_compliance
from parker.core.symbol_inspector import parse_header_declarations
from parker.plugins.ripley_plugin import ParkerPlugin

runner = CliRunner()


def test_parse_header_declarations(tmp_path):
    h = tmp_path / "lib.h"
    h.write_text("""
    #ifndef LIB_H
    #define LIB_H
    
    int calcular_suma(int a, int b);
    static void interna_invalida(void);
    char* obtener_nombre(const char* id);
    
    #endif
    """)
    decls = parse_header_declarations(h.read_text())
    names = [d.name for d in decls]
    assert "calcular_suma" in names
    assert "interna_invalida" in names
    assert "obtener_nombre" in names
    assert next(d for d in decls if d.name == "interna_invalida").is_static is True


def test_check_abi_compliance_header_only(tmp_path):
    h = tmp_path / "tda.h"
    h.write_text("""
    int funcion_correcta(int x);
    static int funcion_estatica_en_h(void);
    """)
    report = check_abi_compliance(h)
    assert len(report.issues) == 1
    assert report.issues[0].code == "PRK001"
    assert report.passed is True  # Warning no rompe build


def test_cli_audit_json(tmp_path):
    h = tmp_path / "test.h"
    h.write_text("int foo(void);")
    res = runner.invoke(app, ["audit", str(h), "--json"])
    assert res.exit_code == 0
    assert '"total_declarations_in_header": 1' in res.output


def test_cli_version():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "PARKER" in res.output


def test_ripley_plugin(tmp_path):
    h = tmp_path / "mod.h"
    h.write_text("int ejecutar(void);")
    plugin = ParkerPlugin()
    res = plugin.run({"source_dir": str(tmp_path)})
    assert res["passed"] is True
    assert "issues" in res
