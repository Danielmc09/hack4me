# app/factories/gemini_creator.py
from app.factories.ia_creator import IAAnalyzerCreator
from app.services.gemini_analyzer import GeminiAnalyzer

class GeminiAnalyzerCreator(IAAnalyzerCreator):
    """
    Concrete Creator para Gemini. Crea GeminiAnalyzer.
    """
    def factory_method(self):
        return GeminiAnalyzer()
