from flask import Flask, app, render_template, request, redirect, url_for, abort, send_from_directory
import os
from werkzeug.utils import secure_filename
import librosa
import matplotlib.pyplot as plt
import librosa.display
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.palettes import YlOrRd
from bokeh.models.annotations import Title

app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3']
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024


def get_chromagram(file, offset=5, duration=5, hop_length=10, n_chroma=200):
    x, sr = librosa.load(
        os.path.join(app.config['UPLOAD_PATH'], file),
        offset=offset, duration=duration)
    chromagram = librosa.feature.chroma_stft(
        x, sr=sr, hop_length=hop_length, n_chroma=n_chroma)
    return chromagram


def plot_chromagram(chromagram, plot_width=800, plot_height=200, reverse_palette=YlOrRd):
    palette = reverse_palette[9][::-1]
    plot = figure(plot_width=plot_width, plot_height=plot_height)
    plot.image(image=[chromagram],
               x=0, y=0, dw=5, dh=1, palette=palette)
    plot.xaxis.axis_label = 'Time (s)'
    plot.yaxis.axis_label = 'Pitch class profile'
    t = Title()
    t.text = 'Chromagram for 5 seconds'
    plot.title = t
    return plot


@app.route('/', methods=['GET'])
def index():
    files = os.listdir(app.config['UPLOAD_PATH'])
    # cleanup files before the first GET request
    for file in files:
        os.remove(os.path.join(app.config['UPLOAD_PATH'], file))
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files)


@app.route('/', methods=['POST'])
def upload_files(result_table='temp'):
    uploaded_file = request.files['audiofile']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            return "Invalid audio file", 400
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        files = os.listdir(app.config['UPLOAD_PATH'])
        chromagrams, scripts, divs, tables = {}, {}, {}, {}
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()
        for file in files:
            curr_chromagram = get_chromagram(file)
            curr_plot = plot_chromagram(curr_chromagram)
            script, div = components(curr_plot)
            chromagrams[file] = curr_chromagram
            scripts[file] = script
            divs[file] = div


        html = render_template('index.html',
                               files=files, js_resources=js_resources,
                               css_resources=css_resources,
                               scripts=scripts,
                               divs=divs)
        return html
    return '', 204


@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)
