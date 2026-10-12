"""Excepciones controladas que la interfaz puede comunicar al analista SQA."""

class PDSError(Exception):
    """Error de negocio del prototipo."""

class InputError(PDSError):
    """CSV inválido o datos incompatibles."""

class ModelError(PDSError):
    """Pipeline ausente, no confiable o incompatible."""

class PersistenceError(PDSError):
    """Fallo de registro de evidencias."""
