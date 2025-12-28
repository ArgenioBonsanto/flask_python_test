import json
from unittest.mock import Mock, patch, MagicMock
from services.documents import Documents, Feedback
from google.genai import errors


class TestDocumentsConvertToJson:

    def test_convert_valid_json_file(self, temp_json_file):
        docs = Documents()
        result = docs.convert_documents_to_json(temp_json_file)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["doc_id"] == 1
        assert "content" in result[0]

    def test_convert_invalid_json_file(self, temp_invalid_json_file):
        docs = Documents()
        result = docs.convert_documents_to_json(temp_invalid_json_file)
        
        assert isinstance(result, str)
        assert "failed to parse JSON" in result

    def test_convert_nonexistent_file(self):
        docs = Documents()
        result = docs.convert_documents_to_json("nonexistent_file.json")
        
        assert isinstance(result, str)
        assert "An error occurred" in result

    def test_convert_empty_json_array(self, tmp_path):
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")
        
        docs = Documents()
        result = docs.convert_documents_to_json(str(empty_file))
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestDocumentsConvertJsonToDocuments:
    def test_convert_valid_data(self, sample_json_data):
        docs = Documents()
        result = docs.convert_json_to_documents(sample_json_data)
        
        assert len(result) == 1
        assert result[0].doc_id == 1
        assert len(result[0].pages) == 2
        assert result[0].pages[0].page_number == 1
        assert result[0].pages[1].page_number == 2

    def test_convert_words_extraction(self, sample_json_data):
        docs = Documents()
        result = docs.convert_json_to_documents(sample_json_data)
        
        page1_words = result[0].pages[0].words
        assert "Hello" in page1_words
        assert "World" in page1_words
        assert "Test" in page1_words



class TestDocumentsAnalizeDocuments:
    @patch('services.documents.genai.Client')
    def test_analize_documents_success(self, mock_client_class, sample_document_model, mock_gemini_response):
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_chunk = Mock()
        mock_chunk.text = json.dumps(mock_gemini_response)
        
        mock_response = [mock_chunk]
        mock_client.models.generate_content_stream.return_value = mock_response
        
        docs = Documents()
        results = list(docs.analize_documents([sample_document_model], "gemini-2.5-flash"))
        
        assert len(results) == 1
        result_data = json.loads(results[0])
        assert "result" in result_data
        assert result_data["result"]["page"] == 1
        assert result_data["result"]["doc_id"] == 1
        assert "others" in result_data["result"]
        assert "reasoning" in result_data["result"]


    @patch('services.documents.genai.Client')
    def test_analize_client_error_quota_exceeded(self, mock_client_class, sample_document_model):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content_stream.side_effect = errors.ClientError(
            code=429, 
            response_json={"error": {"message": "Quota exceeded"}}
        )
        
        docs = Documents()
        results = list(docs.analize_documents([sample_document_model], "gemini-2.5-flash"))
        
        assert len(results) == 1
        result_data = json.loads(results[0])
        assert "error" in result_data
        assert "quota" in result_data["error"].lower()

    @patch('services.documents.genai.Client')
    def test_analize_generic_exception(self, mock_client_class, sample_document_model):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content_stream.side_effect = Exception("Generic error")
        
        docs = Documents()
        results = list(docs.analize_documents([sample_document_model], "gemini-2.5-flash"))
        
        assert len(results) == 1
        result_data = json.loads(results[0])
        assert "error" in result_data
        assert "Generic error" in result_data["error"]


