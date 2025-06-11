# app/services/nmap_scanner.py

import nmap
from app.factories.logger_factory import LoggerFactory

class NmapScanner:
    def __init__(self):
        self.scanner = nmap.PortScanner()
        self.logger = LoggerFactory.create_logger("nmap_scanner")

    def scan_domain(self, domain: str):
        """
        Realiza un escaneo básico de puertos (1-1024) a un dominio.
        """
        result = {}
        try:
            self.logger.info(f"Iniciando escaneo para el dominio: {domain}")
            self.scanner.scan(domain, '1-1024', arguments='-sV')
            for host in self.scanner.all_hosts():
                self.logger.debug(f"Procesando host: {host}")
                result[host] = []
                for proto in self.scanner[host].all_protocols():
                    ports = self.scanner[host][proto].keys()
                    for port in sorted(ports):
                        port_data = self.scanner[host][proto][port]
                        state = port_data['state']
                        service = port_data.get('name', '')
                        product = port_data.get('product', '')
                        version = port_data.get('version', '')
                        result[host].append({
                            'port': port,
                            'state': state,
                            'service': service,
                            'product': product,
                            'version': version
                        })
                        self.logger.debug(f"Puerto {port} encontrado en estado: {state}")
            self.logger.info(f"Escaneo completado para: {domain}")
        except Exception as e:
            self.logger.error(f"Error durante el escaneo de {domain}: {str(e)}")
            result['error'] = str(e)
        return result
        