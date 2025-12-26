from google import genai
from google.genai import types
from google.genai import errors
from pydantic import BaseModel, Field
import json

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
                
                for word_info in page.get("words", []):
                    content = word_info.get("content", "")
                    words.append(content)
                
                pages[num_page] = " ".join(words)
        
        return pages

    def analize_document(self, pages, model):
        try:
            client = genai.Client()
            config_lawyer = types.GenerateContentConfig(
                system_instruction="""
                    You are a helpful lawyer, analyze the text and return the main points. 
                    The response must be coherent, logically structured, contextually accurate, 
                    and easy to understand by a legal professional with no prior knowledge of the matter.
                """,
                response_mime_type="application/json",
                response_json_schema=Feedback.model_json_schema()
            )
            chat = client.chats.create(
                model=model,
                config=config_lawyer
            )

            resume = {}
            for page in pages:
                resume[page] = ""
                response = chat.send_message_stream(pages[page])
                text = ""
                for chunk in response:
                    text += chunk.text
                
                resume[page] = json.loads(text)
                # break #ESTA UNA UNICA PAGINA PARA PRUEBAS, QUITAR ESTE BREAK

            return resume
        except errors.ClientError as e:
            return "You exceeded your current quota, please check your plan and billing details." 
        except Exception as e:
            return str(e.message)


class Feedback(BaseModel):
    summary: str = Field(description="A brief summary of the content.")
    directions: list[str] = Field(description="directions in the document. Only the directions. any more")
    timeline: dict[str, str] = Field(description="A dictionary where the key is the date in format: yyyy/mm/dd and the value is a description of the event. sort from the earliest date to the earliest") 