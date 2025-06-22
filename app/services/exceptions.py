# app/services/exceptions.py

class ScanError(Exception):
    """Errores durante el escaneo con nmap."""

class AnalysisError(Exception):
    """Errores durante el análisis con IA."""

class ReportError(Exception):
    """Errores generando o subiendo reportes PDF."""

class EmailError(Exception):
    """Errores al enviar emails."""
