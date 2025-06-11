# app/services/nmap_scanner.py

from abc import ABC, abstractmethod

class IAAnalyzer(ABC):
    @abstractmethod
    def analyze_scan(self, domain: str, scan_text: str) -> str:
        pass
