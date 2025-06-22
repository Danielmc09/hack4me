#app/factories/scanner_creator.py
from abc import ABC, abstractmethod

class ScannerCreator(ABC):
    @abstractmethod
    def factory_method(self):
        """Devuelve una instancia de un scanner concreto."""
        pass

    def scan(self, domain: str):
        scanner = self.factory_method()
        return scanner.scan_domain(domain)
