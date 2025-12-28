from pydantic import BaseModel
from .page_model import PageModel

class DocumentModel(BaseModel):
    doc_id: int
    pages: list[PageModel]
