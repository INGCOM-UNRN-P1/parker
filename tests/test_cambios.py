"""`parker diff`: cambios de ABI entre dos entregas (revisión 07)."""

import json

from typer.testing import CliRunner

from parker.cli import app
from parker.core.cambios import comparar

runner = CliRunner()


def _lib(d, texto):
    d.mkdir()
    (d / "lista.h").write_text(texto, encoding="utf-8")
    return d


def test_quitada_cambiada_y_nueva(tmp_path):
    antes = _lib(tmp_path / "v1", "int lista_largo(const Lista *l);\nvoid lista_agregar(Lista *l, int v);\nint lista_vieja(void);\n")
    despues = _lib(tmp_path / "v2", "int lista_largo(const Lista *lista);\nvoid lista_agregar(Lista *l, long v);\nint lista_nueva(void);\n")
    codigos = {(i.code, i.symbol_name) for i in comparar(antes, despues).issues}
    assert codigos == {("PRK101", "lista_vieja"), ("PRK102", "lista_agregar"), ("PRK103", "lista_nueva")}


def test_sin_cambios_y_cli(tmp_path):
    antes = _lib(tmp_path / "v1", "int f(int a);\n")
    despues = _lib(tmp_path / "v2", "int  f( int   b );\n")
    assert comparar(antes, despues).passed
    res = runner.invoke(app, ["diff", str(antes), str(despues), "--json"])
    assert res.exit_code == 0 and json.loads(res.stdout)["issues"] == []


def test_normalizacion_de_firmas():
    from parker.core.cambios import _normalizar

    assert _normalizar("int f(int)") == _normalizar("int f(int a)")
    assert _normalizar("char *g(const char * s, size_t n)") == _normalizar("char* g(const char *x, size_t)")
    assert _normalizar("void h(unsigned int)") == _normalizar("void h(unsigned int valor)")
    assert _normalizar("int f(int)") != _normalizar("int f(long)")
