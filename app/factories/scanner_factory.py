from app.services.nmap_scanner import NmapScanner
from app.factories.logger_factory import LoggerFactory

class ScannerFactory:
    logger = LoggerFactory.create_logger("scanner_factory")

    @staticmethod
    def create_scanner(scanner_type: str):
        """
        Devuelve la implementación de scanner según el tipo.
        """
        ScannerFactory.logger.info(f"Creando scanner de tipo: {scanner_type}")
        try:
            if scanner_type == 'nmap':
                return NmapScanner()
            else:
                raise ValueError(f"Tipo de scanner no soportado: {scanner_type}")
        except Exception as e:
            ScannerFactory.logger.error(f"Error al crear scanner: {str(e)}")
            raise
            