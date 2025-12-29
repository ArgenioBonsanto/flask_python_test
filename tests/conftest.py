import pytest
import json
import os
import tempfile
from app import app
from models.others_model import OthersModel
from models.page_model import PageModel
from models.document_model import DocumentModel

@pytest.fixture
def app_fixture():
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app_fixture):
    return app_fixture.test_client()

@pytest.fixture
def sample_json_data():
    return [
        {
            "doc_id": 1,
            "content": [
                {
                    "page_number": 1,
                    "width": 612.0,
                    "height": 792.0,
                    "unit": "pixels",
                    "words": [
                        {"content": "Hello", "confidence": 0.95},
                        {"content": "World", "confidence": 0.91},
                        {"content": "Test", "confidence": 0.97}
                    ]
                },
                {
                    "page_number": 2,
                    "width": 612.0,
                    "height": 792.0,
                    "unit": "pixels",
                    "words": [
                        {"content": "Page", "confidence": 0.92},
                        {"content": "Two", "confidence": 0.45}
                    ]
                }
            ]
        }
    ]

@pytest.fixture
def sample_others_model():
    return OthersModel(
        name="1",
        confidence=0.9,
        width=612.0,
        height=792.0,
        unit="pixels",
        total_pages=2
    )

@pytest.fixture
def sample_page_model(sample_others_model):
    return PageModel(
        page_number=1,
        words=["Hello", "World", "Test"],
        raw_words_data=[
            {"content": "Hello", "confidence": 0.95},
            {"content": "World", "confidence": 0.91},
            {"content": "Test", "confidence": 0.97}
        ],
        others=sample_others_model
    )

@pytest.fixture
def sample_document_model(sample_page_model):
    return DocumentModel(
        doc_id=1,
        pages=[sample_page_model]
    )

@pytest.fixture
def temp_json_file(sample_json_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_json_data, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)

@pytest.fixture
def temp_invalid_json_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json content")
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)

@pytest.fixture
def mock_gemini_response():
    return {
        "reasoning": "The document discusses a sample legal case.",
        "summary": "Sample legal document summary.",
        "timeline": {
            "2024/01/15": "Case filed",
            "2024/02/20": "Hearing scheduled"
        },
        "source_quote": "This is a direct quote from the document."
    }
