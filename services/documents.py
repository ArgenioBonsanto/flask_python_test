import os
import json
import time

from google import genai
from google.genai import types
from google.genai import errors
from pydantic import BaseModel, Field
from flask import stream_with_context
from models.others_model import OthersModel
from models.page_model import PageModel
from models.document_model import DocumentModel


class Documents:

    def convert_documents_to_json(self, filepath):
        try:
            with open(filepath, 'r') as f:
                json_data = json.load(f)

            return json_data

        except json.JSONDecodeError:
            return "File uploaded but failed to parse JSON."
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def convert_json_to_documents(self, data):
        document_list = []
        for doc in data:
            pages = []
            for page in doc.get("content", []):
                num_page = page.get("page_number")
                words = []
                confidence_word = []
                for word_info in page.get("words", []):
                    content = word_info.get("content", "")
                    words.append(content)
                    if word_info.get("confidence") < 0.6:
                        confidence_word.append(content)
                
                others = OthersModel(name=str(doc.get("doc_id")), 
                                    confidence=list(set(confidence_word)), 
                                    width=float(page.get("width")), 
                                    height=float(page.get("height")), 
                                    unit=str(page.get("unit")), 
                                    total_pages=int(len(doc.get("content")))) 
                
                page_model = PageModel(page_number=num_page, 
                                        words=words, 
                                        others=others)

                pages.append(page_model)

            documentModel = DocumentModel(doc_id=int(doc["doc_id"]), 
                                          pages=pages)
            document_list.append(documentModel)

        return document_list

    def analize_documents(self, documents, model):
        try:
            client = genai.Client()
            temperate = 1.0 if "3" in model else 0.0 #Recomendacion de la doc
            config_lawyer = types.GenerateContentConfig(
                system_instruction="""
                    You are a helpful lawyer, analyze the text and return the main points in short. 
                    The response must be coherent, logically structured, contextually accurate, 
                    and easy to understand by a legal professional with no prior knowledge of the matter.
                    answer only based on this text provided
                """,
                response_mime_type="application/json",
                response_json_schema=Feedback.model_json_schema(),
                # temperature=temperate,
                seed=26
            )
            for document in documents:
                all_pages = document.pages
                for page in all_pages:
                    response = client.models.generate_content_stream(
                        model=model,
                        contents=" ".join(page.words),
                        config=config_lawyer
                    )
                    text = ""
                    for chunk in response:
                        text += str(chunk.text)
                    
                    result = json.loads(text)
                    result["page"] = page.page_number
                    result["others"] = page.others.model_dump()
                    result["doc_id"] = document.doc_id
                    yield json.dumps({"result": result})

        except errors.ClientError as e:
            yield json.dumps({"error": "You exceeded your current quota, please check your plan and billing details."})
        except Exception as e:
            yield json.dumps({"error": str(e)})

    @stream_with_context
    def generate_stream(self, filepath, modelSelect):
        try:
            json_data = self.convert_documents_to_json(filepath)
            documents = self.convert_json_to_documents(json_data)
            for chunk in self.analize_documents(documents, modelSelect):
                yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e)})

class Feedback(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning used to analyze the text and extract the details.")
    summary: str = Field(description="A brief summary of the content.")
    timeline: dict[str, str] = Field(description="A dictionary where the key is the date in format: yyyy/mm/dd and the value is a description of the event. sort from the earliest date to the earliest") 
    source_quote: str = Field(description="Exact quote from the document supporting this event.")