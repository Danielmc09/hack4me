# app/models/scan_request.py
from pydantic import BaseModel, EmailStr

class ScanRequest(BaseModel):
    domain: str
    email: EmailStr
    