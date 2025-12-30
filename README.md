# Document Analyzer - Flask & Gemini API

This project is a web application developed with **Flask** designed to receive and analyze JSON documents originating from an OCR process. It leverages the **Gemini API** to process content and generate a brief summary for each document and its pages.

## Features

- **Progressive Analysis**: Real-time visualization of documents being analyzed in the front-end.
- **Intelligent Summaries**: AI-powered brief summaries for each document and page.
- **Page-Level Detail**: Breakdown of relevant information for every page within a document.
- **Data Validation**: Structured and validated information processing.

## Prerequisites

- Python 3.x
- A Google Gemini API Key.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd flask_python_test
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Create a `.env` file in the project root and add your API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### Start the Server
To run the application in development mode, use the following command:
```bash
flask run
```
The application will be available at `http://127.0.0.1:5000/`.

### Run Tests
The project includes a test suite to ensure the correct functioning of services and models:
```bash
pytest
```

## Tech Stack

- **Backend**: Flask
- **AI**: Google Gemini API (google-genai)
- **Validation**: Pydantic
- **Testing**: Pytest
- **Frontend**: HTML/JS (Vanilla)
