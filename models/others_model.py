from pydantic import BaseModel

class OthersModel(BaseModel):
    name: str
    confidence: list[str]
    width: float
    height: float
    unit: str
    total_pages: int
