import json
import os
from unittest.mock import patch, Mock
from io import BytesIO


class TestHomeRoute:
    def test_home_returns_200(self, client):
        response = client.get('/')
        assert response.status_code == 200

class TestUploadRoute:
    def test_upload_with_get_method(self, client):
        response = client.get('/upload')
        assert response.status_code == 405

    def test_upload_no_file_part(self, client):
        response = client.post('/upload', data={'modelSelect': 'gemini-2.5-flash'})
        assert response.status_code == 200
        assert b'No file part' in response.data

    def test_upload_empty_filename(self, client):
        data = {
            'file': (BytesIO(b''), ''),
            'modelSelect': 'gemini-2.5-flash'
        }
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert b'No file selected' in response.data

    def test_upload_invalid_file_type(self, client):
        data = {
            'file': (BytesIO(b'test content'), 'test.txt'),
            'modelSelect': 'gemini-2.5-flash'
        }
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert b'Invalid file type' in response.data

    @patch('app.Documents')
    def test_upload_valid_json_file(self, mock_documents_class, client, sample_json_data):
        mock_docs = Mock()
        mock_documents_class.return_value = mock_docs
        mock_docs.generate_stream.return_value = [
            json.dumps({"result": {"page": 1, "summary": "Test"}})
        ]
        
        json_content = json.dumps(sample_json_data).encode('utf-8')
        data = {
            'file': (BytesIO(json_content), 'test.json'),
            'modelSelect': 'gemini-2.5-flash'
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        assert response.status_code == 200
        assert response.mimetype == 'text/plain'
        assert mock_documents_class.called
        assert mock_docs.generate_stream.called

    @patch('app.Documents')
    def test_upload_creates_uploads_directory(self, mock_documents_class, client, sample_json_data, tmp_path):
        mock_docs = Mock()
        mock_documents_class.return_value = mock_docs
        mock_docs.generate_stream.return_value = [json.dumps({"result": {}})]
        
        json_content = json.dumps(sample_json_data).encode('utf-8')
        data = {
            'file': (BytesIO(json_content), 'test.json'),
            'modelSelect': 'gemini-2.5-flash'
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert os.path.exists('uploads')

    @patch('app.Documents')
    def test_upload_file_is_saved(self, mock_documents_class, client, sample_json_data):
        mock_docs = Mock()
        mock_documents_class.return_value = mock_docs
        mock_docs.generate_stream.return_value = [json.dumps({"result": {}})]
        
        json_content = json.dumps(sample_json_data).encode('utf-8')
        filename = 'test_save.json'
        data = {
            'file': (BytesIO(json_content), filename),
            'modelSelect': 'gemini-2.5-flash'
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        
        filepath = os.path.join('uploads', filename)
        assert os.path.exists(filepath)
        
        if os.path.exists(filepath):
            os.remove(filepath)


    @patch('app.Documents')
    def test_upload_streaming_response(self, mock_documents_class, client, sample_json_data):
        mock_docs = Mock()
        mock_documents_class.return_value = mock_docs
        
        mock_docs.generate_stream.return_value = [
            json.dumps({"result": {"page": 1}}),
            json.dumps({"result": {"page": 2}})
        ]
        
        json_content = json.dumps(sample_json_data).encode('utf-8')
        data = {
            'file': (BytesIO(json_content), 'test.json'),
            'modelSelect': 'gemini-2.5-flash'
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        
        response_data = response.data.decode('utf-8')
        assert 'page' in response_data

    @patch('app.Documents')
    def test_upload_handles_processing_errors(self, mock_documents_class, client, sample_json_data):
        mock_docs = Mock()
        mock_documents_class.return_value = mock_docs
        mock_docs.generate_stream.return_value = [
            json.dumps({"error": "Processing failed"})
        ]
        
        json_content = json.dumps(sample_json_data).encode('utf-8')
        data = {
            'file': (BytesIO(json_content), 'test.json'),
            'modelSelect': 'gemini-2.5-flash'
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert b'error' in response.data
