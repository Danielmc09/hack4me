import nmap

class NmapScanner:
    def __init__(self):
        self.scanner = nmap.PortScanner()

    def scan_domain(self, domain: str):
        """
        Realiza un escaneo básico de puertos (1-1024) a un dominio.
        """
        result = {}
        try:
            self.scanner.scan(domain, '1-1024')
            for host in self.scanner.all_hosts():
                result[host] = []
                for proto in self.scanner[host].all_protocols():
                    ports = self.scanner[host][proto].keys()
                    for port in sorted(ports):
                        state = self.scanner[host][proto][port]['state']
                        result[host].append({
                            'port': port,
                            'state': state
                        })
        except Exception as e:
            result['error'] = str(e)
        return result
        