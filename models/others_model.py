from pydantic import BaseModel

class OthersModel(BaseModel):
    name: str
    confidence: float
    width: float
    height: float
    unit: str
    total_pages: int
