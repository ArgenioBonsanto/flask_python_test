import os


from flask import Flask, request
from flask import render_template
from flask import Response
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
            return 'No file selected'
        
        if not file.filename.lower().endswith('.json'):
            return 'Invalid file type. Only .json files are allowed'

        if file:
            filename = file.filename
            content_type = file.content_type
            
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            documents = Documents()
            return Response(documents.generate_stream(filepath, modelSelect), mimetype='text/plain')
        else:
            return 'No file selected'

    else:
        return 'Invalid request method'
