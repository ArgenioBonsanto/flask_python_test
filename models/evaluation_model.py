from pydantic import BaseModel, Field

class EvaluationModel(BaseModel):
    is_faithful: bool = Field(description="True if the response is based ONLY on the provided text.")
    score: float = Field(description="A quality score between 0 and 1, where 1 is perfect faithfulness.")
    explanation: str = Field(description="Brief explanation of the evaluation result.")
