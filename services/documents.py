import os
import json

from google import genai
from google.genai import types
from google.genai import errors
from pydantic import BaseModel, Field
from flask import stream_with_context

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

    def convert_json_to_pages(self, data):
        pages = {}
        for doc in data:
            for page in doc.get("content", []):
                num_page = page.get("page_number")
                words = []
                confidence_word = []
                for word_info in page.get("words", []):
                    content = word_info.get("content", "")
                    words.append(content)
                    if word_info.get("confidence") < 0.6:
                        confidence_word.append(content)
                
                pages[num_page] = {}
                pages[num_page]["words"] = " ".join(words)
                pages[num_page]["others"] = {
                    "name": page.get("name"),
                    "confidence": confidence_word,
                    "width": page.get("width"),
                    "height": page.get("height"),
                    "unit": page.get("unit"),
                    "total_pages": len(pages)
                }

        return pages

    def analize_document(self, pages, model):
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
            chat = client.chats.create(
                model=model,
                config=config_lawyer
            )

            resume = {}
            for page_num, page_content in pages.items():
                response = chat.send_message_stream(page_content["words"])
                text = ""
                for chunk in response:
                    text += str(chunk.text)
                
                result = json.loads(text)
                result["page"] = page_num
                result["others"] = page_content["others"]
                yield json.dumps({"result": result})
        except errors.ClientError as e:
            yield json.dumps({"error": "You exceeded your current quota, please check your plan and billing details."})
        except Exception as e:
            yield json.dumps({"error": str(e)})

    @stream_with_context
    def generate_stream(self, filepath, modelSelect):
        try:
            json_data = self.convert_documents_to_json(filepath)
            pages = self.convert_json_to_pages(json_data)

            for chunk in self.analize_document(pages, modelSelect):
                yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e)})




class Feedback(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning used to analyze the text and extract the details.")
    summary: str = Field(description="A brief summary of the content.")
    timeline: dict[str, str] = Field(description="A dictionary where the key is the date in format: yyyy/mm/dd and the value is a description of the event. sort from the earliest date to the earliest") 
    source_quote: str = Field(description="Exact quote from the document supporting this event.")