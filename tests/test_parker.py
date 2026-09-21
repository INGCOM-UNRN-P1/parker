"""Tests unitarios y de integración para PARKER."""

import json
from pathlib import Path
from typer.testing import CliRunner
from parker.cli import app
from parker.core.abi_checker import check_abi_compliance
from parker.core.symbol_inspector import parse_header_declarations
from parker.plugins.ripley_plugin import ParkerPlugin

runner = CliRunner()


def test_cli_doctor():
    res = runner.invoke(app, ["doctor"])
    assert res.exit_code == 0
    assert "doctor" in res.output.lower()

    res_json = runner.invoke(app, ["doctor", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["herramienta"] == "parker"
    assert data["ok"] is True


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
    assert runner.invoke(app, ["version"]).exit_code != 0  # PARKER-D0402: ya no es subcomando
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "PARKER" in res.output


def test_ripley_plugin(tmp_path):
    h = tmp_path / "mod.h"
    h.write_text("int ejecutar(void);")
    plugin = ParkerPlugin()
    res = plugin.run({"source_dir": str(tmp_path)})
    assert res["passed"] is True
    assert "issues" in res


def test_readme_solo_promete_las_herramientas_que_se_invocan():
    """PARKER-D0801: solo `nm` se invoca; el README no debe prometer readelf/objdump/.dll."""
    raiz = Path(__file__).resolve().parents[1]
    fuente = (raiz / "src/parker/core/symbol_inspector.py").read_text(encoding="utf-8")
    readme = (raiz / "README.md").read_text(encoding="utf-8")
    invocadas = {t for t in ("nm", "readelf", "objdump") if f'"{t}"' in fuente or f"'{t}'" in fuente}
    assert invocadas == {"nm"}
    requisitos = readme.split("### Dependencias Externas y Binarios")[1].split("###")[0]
    assert "nm" in requisitos
    for t in ("readelf", "objdump"):
        assert f"`{t}` u" not in requisitos and "no se usan" in requisitos
    assert "`.so` / `.dll`" not in readme
    r = CliRunner().invoke(app, ["doctor", "--json"])
    assert "readelf" not in r.output
