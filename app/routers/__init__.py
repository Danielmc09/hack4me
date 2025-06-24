# app/services/__init__.py
from abc import ABC, abstractmethod

class Scanner(ABC):
    @abstractmethod
    def scan_domain(self, domain: str) -> dict:
        """
        Escanea un dominio y devuelve los resultados.
        """
        pass

class IAAnalyzer(ABC):
    @abstractmethod
    def analyze_scan(self, domain: str, scan: dict) -> dict:
        """
        Analiza los resultados de un escaneo y devuelve un diccionario con los resultados.
        """
        pass
