# PARKER — Auditor de Estabilidad de ABI y Visibilidad de Símbolos en C

**PARKER** es un linter y evaluador de interfaces binarias (ABI) en C. Audita bibliotecas compartidas (`.so`), archivos objeto (`.o`) y cabeceras (`.h`) para detectar fugas de símbolos privados, símbolos faltantes y malas prácticas en interfaces públicas.

---

## 🎯 Alcance

### Qué cubre
- Auditoría de Application Binary Interface (ABI) y control de visibilidad de símbolos en bibliotecas compartidas y objetos C en ELF (`.so` / `.o`). Los `.dll` de Windows no se inspeccionan.
- Detección de fuga de símbolos internos: advertencia sobre funciones globales no documentadas que carecen del calificador `static`.
- Verificación de consistencia entre prototipos de funciones públicas de la cabecera `.h` y la tabla de exportación de símbolos en el binario compilado.

### Qué no cubre (Límites y Delegación)
- Verificación de opacidad de TDAs en código fuente (delegado a `motoko`).
- Auditoría de alineación y padding de structs (delegado a `brett`).
- Medición de costos de saltos o tablas de salto (delegado a `rachel`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Linux / WSL / POSIX. Python >= 3.10.

### Dependencias Externas y Binarios
- `nm` (binutils). Es la única herramienta que parker invoca; `readelf` y `objdump` no se usan.

### Integración en el Ecosistema
- CLI `parker`. Plugin registrado en `ripley.plugins` (`abi_audit`).

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
