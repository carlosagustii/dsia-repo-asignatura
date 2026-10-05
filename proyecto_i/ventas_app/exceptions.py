"""Excepciones de dominio del pipeline de ventas."""


class VentasError(Exception):
    """Raíz de todos los errores del paquete (permite capturarlos de una vez)."""


class DataLoadError(VentasError):
    """El origen de datos no existe, está vacío o no se puede leer."""


class SchemaError(DataLoadError):
    """El fichero se lee, pero le faltan columnas obligatorias."""


class ValidationError(VentasError):
    """Los datos no cumplen las reglas de negocio de forma irrecuperable."""
