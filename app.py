import os


from flask import Flask, request
from flask import render_template
import json
from dotenv import load_dotenv
from services.documents import Documents

app = Flask(__name__)
load_dotenv()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        modelSelect = request.form.get('modelSelect')
        
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = file.filename
            content_type = file.content_type
            
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            
            try:
                documents = Documents()
                json_data = documents.convert_documents_to_json(filepath)
                pages = documents.convert_json_to_pages(json_data)
                resume = documents.analize_document(pages, modelSelect)
                
                if isinstance(resume, str):
                    return render_template('error.html', error=resume)
                    
                return render_template('results.html', resume=resume, filename=filename)
            except Exception as e:
                return render_template('error.html', error=str(e))
    