from pydantic import BaseModel, Field

class FeedbackModel(BaseModel):
    reasoning: str = Field(description="""-Step-by-step reasoning used to analyze the text and extract the details.\n
                                          -if the text is unreadable, state that the document is unreadable.\n
                                          -If any of those values are inside [[ ]] or {{ }}, explain the document have word whit low confidence.\n
                                          -State if the sentences have logical flow.\n
                                          -If you cannot find a clear message, state 'Information insufficient'.\n
                                          """)
    summary: str = Field(description="A brief summary of the content.")
    timeline: dict[str, str] = Field(description="""-A dictionary where the key is the date and the value is a description of the event.\n
                                                    -the key of the dictionary must be THE SAME DATE HOW ITS WRITE IN THE DOCUMENT.\n
                                                    -Don't change the words what you put in the key of the dictionary, example (14-Oct-2023, 14/10/2023, 14 octuber 2023, 16th MAY 1974).\n
                                                    -Don't include hours in the key of the dictionary
                                                """) 
    analysis_context: str = Field(description="""Compare your summary with the contents of the document, 
                                                 if there are any contradictions, explain them. if not DONT RETURN ANYTHING,
                                                 Don't include nothing about curly brackets or brackets""")