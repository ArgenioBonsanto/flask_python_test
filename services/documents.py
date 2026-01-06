import json

from google import genai
from google.genai import types
from google.genai import errors
from flask import stream_with_context
from models.others_model import OthersModel
from models.page_model import PageModel
from models.document_model import DocumentModel
from models.evaluation_model import EvaluationModel
from models.feedback_model import FeedbackModel
from flask import current_app


class Documents:

    def convert_documents_to_json(self, filepath):
        """
        Reads a JSON file from the given filepath and returns its content.
        
        Args:
            filepath (str): The absolute path to the JSON file to be read.
            
        Returns:
            dict or str: The parsed JSON data if successful, or an error message string if parsing fails or an exception occurs.
        """
        current_app.logger.info(f"convert_documents_to_json: {filepath}")
        try:
            with open(filepath, 'r') as f:
                json_data = json.load(f)

            return json_data

        except json.JSONDecodeError:
            return "File uploaded but failed to parse JSON."
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def convert_json_to_documents(self, data):
        """
        Processes raw OCR JSON data into a structured list of DocumentModel objects.
        
        This method iterates through the provided JSON data, calculates average confidence for each page,
        and marks words based on their OCR confidence levels (low confidence words are wrapped in 
        double brackets [[]] or double curly braces {{}}).
        
        Args:
            data (list): A list of dictionaries representing documents and their OCR-extracted content.
            
        Returns:
            list: A list of DocumentModel objects containing structured page and word data.
        """
        current_app.logger.info(f"convert_json_to_documents: {data}")
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
        """
        Analyzes a list of DocumentModel objects using a Gemini AI model and yields the results.
        
        For each page in each document, it constructs a prompt for the legal-specialized Gemini model,
        streams the response, validates the JSON format, and evaluates the generated summary for faithfulness.
        
        Args:
            documents (list): A list of DocumentModel objects to be analyzed.
            model (str): The identifier of the Gemini model to use for analysis.
            
        Yields:
            str: A JSON-formatted string containing the analysis results, evaluation, or error messages.
        """
        current_app.logger.info("analize_documents")
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
                        response_json_schema=FeedbackModel.model_json_schema(),
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

                    evaluation = self.evaluate_response(client, model, " ".join(page.words), result["summary"])
                    if evaluation:
                        result["evaluation"] = evaluation.model_dump()

                    yield json.dumps({"result": result})

                    # break
                # break
    #change to test
        except errors.ClientError as e:
            yield json.dumps({"error": "You exceeded your current quota, please check your plan and billing details."})
        except Exception as e:
            yield json.dumps({"error": str(e)})

    def evaluate_response(self, client, model, source_text, generated_summary):
        """
        Evaluates the generated summary for faithfulness and hallucinations relative to the source text.
        
        Uses a separate Gemini prompt to act as an expert legal auditor and validates the result
        against the EvaluationModel schema.
        
        Args:
            client (genai.Client): The Google GenAI client instance.
            model (str): The identifier of the Gemini model to use for evaluation.
            source_text (str): The original OCR text used to generate the summary.
            generated_summary (str): The summary generated by the initial analysis.
            
        Returns:
            EvaluationModel or None: A validated EvaluationModel object if successful, otherwise None.
        """
        current_app.logger.info("evaluate_response")
        try:
            config_judge = types.GenerateContentConfig(
                system_instruction="""
                    You are an expert legal auditor. Your task is to evaluate the faithfulness and accuracy of a summary and reasoning against a source legal text.
                    
                    Evaluation Criteria:
                    1. Faithfulness: Is every statement in the generated response supported by the source text?
                    2. Hallucinations: Does the response include information not present in the source?
                    
                    Return your evaluation as a JSON object following the EvaluationModel schema.
                """,
                response_mime_type="application/json",
                response_json_schema=EvaluationModel.model_json_schema(),
                seed=26
            )

            prompt = f"""
                SOURCE TEXT:
                {source_text}
                
                GENERATED RESPONSE TO EVALUATE:
                Summary: {generated_summary}
            """

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config_judge
            )

            if response.text:
                return EvaluationModel.model_validate_json(response.text)
            return None

        except Exception as e:
            print(f"Evaluation failed: {str(e)}")
            return None

    @stream_with_context
    def generate_stream(self, filepath, modelSelect):
        """
        Orchestrates the conversion and analysis of a document file in a streaming.
        
        This is the main entry point for the analysis flow, handling JSON conversion,
        document structure creation, and initiating the analysis stream.
        
        Args:
            filepath (str): The path to the document JSON file.
            modelSelect (str): The model identifier chosen for analysis.
            
        Yields:
            str: Chunks of JSON-formatted analysis results or error messages.
        """
        current_app.logger.info("generate_stream")
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

