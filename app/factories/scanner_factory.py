from app.services.nmap_scanner import NmapScanner

class ScannerFactory:
    @staticmethod
    def create_scanner(scanner_type: str):
        """
        Devuelve la implementación de scanner según el tipo.
        """
        if scanner_type == 'nmap':
            return NmapScanner()
        else:
            raise ValueError(f"Tipo de scanner no soportado: {scanner_type}")
            