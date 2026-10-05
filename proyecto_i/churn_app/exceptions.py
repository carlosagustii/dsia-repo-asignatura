"""Excepciones de dominio del pipeline de churn."""


class ChurnAppError(Exception):
    """Raíz de todos los errores del paquete."""


class DataLoadError(ChurnAppError):
    """El origen de datos no existe, está vacío o no se puede leer."""


class SchemaError(DataLoadError):
    """El fichero se lee, pero le faltan columnas obligatorias."""


class ValidationError(ChurnAppError):
    """Los datos no se pueden validar (p. ej. estructura inesperada)."""
