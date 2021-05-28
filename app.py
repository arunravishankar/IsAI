from flask import Flask, app, render_template, request, redirect, url_for, abort, send_from_directory
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3']
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024


@app.route('/', methods=['GET'])
def index():
    files = os.listdir(app.config['UPLOAD_PATH'])
    # cleanup files before the first GET request
    for file in files:
        os.remove(os.path.join(app.config['UPLOAD_PATH'], file))
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files)
    

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['audiofile']
    filename = secure_filename(uploaded_file.filename)
    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files)


@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)
