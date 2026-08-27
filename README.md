# PARKER — Auditor de Estabilidad de ABI y Visibilidad de Símbolos en C

**PARKER** es un linter y evaluador de interfaces binarias (ABI) en C. Audita bibliotecas compartidas (`.so`), archivos objeto (`.o`) y cabeceras (`.h`) para detectar fugas de símbolos privados, símbolos faltantes y malas prácticas en interfaces públicas.

---

## 🚀 Uso Rápido

```bash
# Auditar solo cabecera
parker audit tda_lista.h

# Contrastar cabecera contra biblioteca compilada
parker audit tda_lista.h --binary libtda_lista.so

# Salida estructurada JSON
parker audit tda_lista.h --json
```

---

## 🔍 Reglas Auditadas

- **`PRK001`**: Funciones declaradas `static` dentro de cabeceras públicas.
- **`PRK002`**: Símbolos exportados en la biblioteca sin declaración en la cabecera (fuga de ABI).
- **`PRK003`**: Símbolos declarados en cabecera pública no encontrados en la biblioteca compilada.
