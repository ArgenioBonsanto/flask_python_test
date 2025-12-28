from pydantic import BaseModel
from .others_model import OthersModel

class PageModel(BaseModel):
    page_number: int
    words: list[str]
    others: OthersModel
