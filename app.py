from flask import Flask, app, render_template, request, redirect, url_for, abort, send_from_directory

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')