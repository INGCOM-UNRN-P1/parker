"""Modelos de datos para el análisis de ABI en PARKER."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SymbolVisibility(str, Enum):
    DEFAULT = "default"
    HIDDEN = "hidden"
    PROTECTED = "protected"
    INTERNAL = "internal"


class SymbolType(str, Enum):
    FUNCTION = "function"
    VARIABLE = "variable"
    UNKNOWN = "unknown"


class ExportedSymbol(BaseModel):
    name: str
    symbol_type: SymbolType
    visibility: SymbolVisibility = SymbolVisibility.DEFAULT
    is_defined: bool = True
    section: Optional[str] = None


class HeaderDeclaration(BaseModel):
    name: str
    return_type: str
    signature: str
    line_number: int
    is_static: bool = False
    has_visibility_attribute: bool = False


class AbiIssue(BaseModel):
    code: str
    severity: str  # "ERROR", "WARNING", "INFO"
    symbol_name: str
    message: str
    location: str
    suggestion: str


class AbiReport(BaseModel):
    library_path: Optional[str] = None
    header_path: Optional[str] = None
    total_symbols_exported: int = 0
    total_declarations_in_header: int = 0
    issues: List[AbiIssue] = Field(default_factory=list)
    passed: bool = True
