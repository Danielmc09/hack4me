# app/services/gemini_analyzer.py

import os
import requests
import json
import re
from datetime import datetime
from app.services.ia_service import IAAnalyzer
from app.factories.logger_factory import LoggerFactory

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HEADERS_GEMINI = {"Content-Type": "application/json"}

class GeminiAnalyzer(IAAnalyzer):
    def __init__(self):
        self.logger = LoggerFactory.create_logger("gemini_analyzer")

    def analyze_scan(self, domain: str, scan_text: str) -> dict:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

            prompt = f"""
            You are a cybersecurity expert and an OSCP exam report writer.
            You will receive an Nmap scan for the domain: {domain}.

            Generate a JSON analysis in English with these sections:
            - table_of_contents (as a list of strings)
            - summary
            - objective
            - requirements (as a list of strings)
            - high_level_summary
            - recommendations (as a list of strings)
            - methodology (as a list of objects with 'title', 'description', and 'evidence')
            - vulnerabilities (as a list of objects with 'cve_id' and 'severity')
            - penetration (as a list of vulnerabilities with 'vulnerability_exploited', 'system_vulnerable', 'description', 'severity', 'proof_of_concept')
              - NOTE: If no penetration testing was performed, map vulnerabilities from the vulnerabilities section into penetration to avoid empty findings.
            - maintaining_access
            - house_cleaning
            - additional_notes

            IMPORTANT: 
            - Return valid JSON **directly** (no code blocks, no triple backticks).
            - Do **NOT** wrap JSON as a string inside the JSON.
            - Each JSON field should contain its native type (arrays, objects).
            - If 'summary' is empty, fill it with a placeholder.
            - If 'requirements' is a single string, convert it to a list with that single item.
            - If 'penetration' is empty but 'vulnerabilities' exists, map vulnerabilities into penetration automatically.

            Here is the scan result:
            --------------------
            {scan_text}
            --------------------
            """

            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            self.logger.info(f"🚀 Sending analysis to Gemini.")
            response = requests.post(
                f"{url}?key={GEMINI_API_KEY}",
                headers=HEADERS_GEMINI,
                json=payload,
                timeout=400
            )
            response.raise_for_status()
            result = response.json()
            self.logger.info(f"✅ Gemini response: {result}")

            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            # Limpiar delimitadores de Markdown ```json ... ```
            if text.startswith("```json"):
                text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.DOTALL).strip()

            # Deserializar si Gemini devuelve JSON serializado como string
            if text.startswith('"') and text.endswith('"'):
                try:
                    text = json.loads(text)
                except Exception as e:
                    self.logger.error(f"❌ Error deserializing Gemini response (nested string): {e}")
                    text = text.strip('"')

            try:
                parsed_result = json.loads(text)
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Error parsing Gemini JSON: {e}")
                parsed_result = {}

            if isinstance(parsed_result, dict):
                parsed_result.setdefault("domain", domain)
                parsed_result.setdefault("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
                parsed_result.setdefault("summary", "No summary available.")
                parsed_result.setdefault("requirements", ["No requirements specified."])
                parsed_result.setdefault("recommendations", [])
                parsed_result.setdefault("methodology", [])
                parsed_result.setdefault("service_enumeration", [])
                parsed_result.setdefault("penetration", [])
                parsed_result.setdefault("vulnerabilities", [])

                # Convertir requirements a lista si es string
                if isinstance(parsed_result.get("requirements"), str):
                    parsed_result["requirements"] = [parsed_result["requirements"]]

                # Si no hay penetración pero hay vulnerabilidades, crear penetración
                if not parsed_result["penetration"] and parsed_result["vulnerabilities"]:
                    parsed_result["penetration"] = [
                        {
                            "vulnerability_exploited": vuln.get("cve_id", "Unknown CVE"),
                            "system_vulnerable": domain,
                            "description": "No detailed exploitation provided.",
                            "severity": vuln.get("severity", "Unknown"),
                            "proof_of_concept": "No PoC provided."
                        }
                        for vuln in parsed_result["vulnerabilities"]
                    ]

                return parsed_result
            else:
                raise ValueError("Gemini's response is not a valid JSON dictionary.")
        except Exception as e:
            self.logger.error(f"❌ Error processing Gemini response: {e}")
            return {
                "summary": f"Error: {e}",
                "objective": "",
                "requirements": ["No requirements specified."],
                "high_level_summary": "",
                "recommendations": [],
                "methodology": [],
                "information_gathering": "",
                "service_enumeration": [],
                "penetration": [],
                "maintaining_access": "",
                "house_cleaning": "",
                "additional_notes": "",
                "vulnerabilities": []
            }
