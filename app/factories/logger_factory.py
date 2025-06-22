from logging import Logger, getLogger, StreamHandler, Formatter
import logging.handlers
import os

class LoggerFactory:
    @staticmethod
    def create_logger(logger_name: str, log_level: str = "INFO") -> Logger:
        """Crea y configura un logger según el tipo especificado"""
        # Crear el logger
        logger = getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level))

        # Evitar duplicación de handlers
        if logger.handlers:
            return logger

        # Crear el directorio de logs si no existe
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # Configurar el formato
        formatter = Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler para archivo
        file_handler = logging.handlers.RotatingFileHandler(
            f"{log_dir}/{logger_name}.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Handler para consola
        console_handler = StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger
        