import json

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
            for page in doc.get("content"):
                num_page = page.get("page_number")
                words = []
                confidence_amount = 0;
                for word_info in page.get("words"):
                    content = word_info.get("content")
                    confidence = word_info.get("confidence")
                    confidence_amount += confidence
                    if 0.80 <= confidence <= 0.90:
                        words.append(f"[[{content}]]")
                    elif confidence < 0.80:
                         words.append("{{" + content+ "}}")
                    else:
                        words.append(content)

                avg_conf = round(confidence_amount / len(page.get("words")), 2)
                
                others = OthersModel(name=str(doc.get("doc_id")), 
                                    confidence=float(avg_conf), 
                                    width=float(page.get("width")), 
                                    height=float(page.get("height")), 
                                    unit=str(page.get("unit")), 
                                    total_pages=int(len(doc.get("content")))) 
                
                page_model = PageModel(page_number=num_page, 
                                        words=words, 
                                        raw_words_data=page.get("words"),
                                        others=others)

                pages.append(page_model)

            documentModel = DocumentModel(doc_id=int(doc["doc_id"]), 
                                          pages=pages)
            document_list.append(documentModel)

        return document_list

    def analize_documents(self, documents, model):
        try:
            client = genai.Client()
            for document in documents:
                all_pages = document.pages
                for page in all_pages:
                    quality_note = ""
                    avg_conf = page.others.confidence
                    average_quality = f"-The average OCR quality of the document is {avg_conf}\n"
                    if avg_conf < 0.90:
                        average_quality += "[SYSTEM NOTE: put in the summary field EXCLUSIVELY THE WORDS: 'the document has very low OCR quality' and put in the timeline field EXCLUSIVELY THE WORDS: '' (empty string)]\n"
                    config_lawyer = types.GenerateContentConfig(
                        system_instruction=f"""
                            -You are a helpful lawyer, analyze the text and return the main points in short.\n
                            -Analyze the provided text, which comes from an OCR process.\n
                            -Note: All words have a confidence between 0 and 1.\n
                            -Words in two brackets (e.g., [[word]]) have confidence between 0.80 and 0.90 are low-confidence detections.\n
                            -Words in two curly braces "{{word}}" are low-confidence detections, less than 0.8. high posibility to be ILLEGIBLE.\n
                            -If a key legal term or fact is ambiguous or unreadable, do not guess. \n
                            -Instead, state in the analysis field that certain information on page X is illegible or unclear.\n
                            -Priority is accuracy over completion.\n
                            -The response must be coherent, logically structured, contextually accurate, 
                            and easy to understand by a legal professional with no prior knowledge of the matter.\n
                            -Answer only based on this text provided.\n
                            -Evaluate if the text quality allows for a reliable legal interpretation.\n
                            -the field analysis_context only used if The average quality of the document is less than 0.90., If higher than 0.90, return an empty string, if less than 0.90 dont include the [[ILLEGIBLE]] word\n
                            -Return the response as a single JSON array containing objects for each section. Do not output multiple separate JSON blocks.
                            {average_quality}
                        """,
                        response_mime_type="application/json",
                        response_json_schema=Feedback.model_json_schema(),
                        seed=26
                    )

                    response = client.models.generate_content_stream(
                        model=model,
                        contents=" ".join(page.words),
                        config=config_lawyer
                    )
                    text = ""
                    for chunk in response:
                        if(chunk.text is not None):
                            text += str(chunk.text)

                    if(len(text.strip()) == 0):
                        continue
                    try:
                        result = json.loads(text)
                    except Exception as e:
                         yield json.dumps({"error": "Google Error json format"})
                         continue

                    result["page"] = page.page_number
                    result["others"] = page.others.model_dump()
                    result["doc_id"] = document.doc_id
                    yield json.dumps({"result": result})

                    # break
                # break

        except errors.ClientError as e:
            yield json.dumps({"error": "You exceeded your current quota, please check your plan and billing details."})
        except Exception as e:
            yield json.dumps({"error": str(e)})

    @stream_with_context
    def generate_stream(self, filepath, modelSelect):
        try:
            json_data = self.convert_documents_to_json(filepath)
            try:
                documents = self.convert_json_to_documents(json_data)
            except Exception as e:
                yield json.dumps({"error": "Invalid JSON format"})
                return
            
            for chunk in self.analize_documents(documents, modelSelect):
                yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e)})

class Feedback(BaseModel):
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