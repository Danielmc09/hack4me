# app/factories/nmap_creator.py
from app.factories.scanner_creator import ScannerCreator
from app.services.nmap_scanner import NmapScanner

class NmapScannerCreator(ScannerCreator):
    """
    Concrete Creator para Nmap. Crea NmapScanner.
    """
    def factory_method(self):
        return NmapScanner()
