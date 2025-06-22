# app/factories/ia_creator.py
from abc import ABC, abstractmethod
from app.services.ia_service import IAAnalyzer

class IAAnalyzerCreator(ABC):
    """
    Creator abstracto: declara factory_method() que devuelve un IAAnalyzer.
    """

    @abstractmethod
    def factory_method(self) -> IAAnalyzer:
        pass

    def analyze(self, domain: str, scan_result: dict) -> dict:
        """
        Template method: usa factory_method() para crear el analyzer
        y ejecuta analyze_scan.
        """
        analyzer = self.factory_method()
        return analyzer.analyze_scan(domain, scan_result)
