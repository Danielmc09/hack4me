# app/factories/ia_factory.py

from app.services.ia_service import IAAnalyzer
from app.services.gemini_analyzer import GeminiAnalyzer
# En el futuro aquí podrías importar GPTAnalyzer, ClaudeAnalyzer, etc.

class IAFactory:
    @staticmethod
    def create_analyzer(model_name: str = "gemini") -> IAAnalyzer:
        if model_name == "gemini":
            return GeminiAnalyzer()
        else:
            raise ValueError(f"Modelo IA '{model_name}' no soportado.")
