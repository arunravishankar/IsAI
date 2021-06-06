from flask import Flask, app, render_template, request, redirect, url_for, abort, send_from_directory
import os
from werkzeug.utils import secure_filename
import librosa
import librosa.display
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import INLINE
from bokeh.palettes import YlOrRd
from bokeh.models.annotations import Title
from json2html import *
import pickle
import numpy as np
import sklearn
import warnings
import pandas as pd

warnings.filterwarnings("ignore")


app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'uploads'
#app.config['UPLOAD_EXTENSIONS'] = ['.wav', '.mp3']
app.config['UPLOAD_EXTENSIONS'] = ['.wav']
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024


def extract_feature(file_name, i):
    X, sample_rate = librosa.load(file_name, offset = 20*i, duration = 10)
    stft = np.abs(librosa.stft(X))
    mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40).T,axis=0)
    chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T,axis=0)
    mel = np.mean(librosa.feature.melspectrogram(X, sr=sample_rate).T,axis=0)
    contrast = np.mean(librosa.feature.spectral_contrast(S=stft,
    	sr=sample_rate).T,axis=0)
    tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(X),
    	sr=sample_rate).T,axis=0)
    return mfccs,chroma,mel,contrast,tonnetz


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
    if not os.path.exists(app.config['UPLOAD_PATH']):
        os.makedirs(app.config['UPLOAD_PATH'])
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
            # Run through the model to obtain ragam
            modelfile = os.path.join('ml', 'ridge_model')
            loaded_model = pickle.load(open(modelfile, 'rb'))
            features_test = np.empty((0,193))
            for i in range(10):
                try:
                    mfccs, chroma, mel, contrast, tonnetz = extract_feature(os.path.join(app.config['UPLOAD_PATH'], file),i)
                    ext_features = np.hstack([mfccs, chroma, mel, contrast, tonnetz])
                    features_test = np.vstack([features_test, ext_features])
                except:
                    pass
            pred = list(loaded_model.predict(features_test))
            pred_ragam = max(pred, key=pred.count)
            print(pred_ragam)

            df = pd.read_csv(os.path.join('data_utils', 'sample_min_rag_100_samp_100_50_df.csv'))
            df = df[df['Ragam']==pred_ragam]
            columns = ['Kriti', 'Ragam', 'Composer', 'Main Artist', 'Download URLs']
            df = df[columns]
            df = df.drop_duplicates('Kriti')
            
            try:
                related_table = {"Related Links": list(df.T.to_dict().values())[:5]}
                
            except:
                result_table = 'temp'
                related_links = ["https://www.sangeethamshare.org/tvg/UPLOADS-1001---1200/1172-T.N.Seshagopalan_7-Navarathnamalika-4-Podhigai_TV/",
                                "https://www.sangeethamshare.org/tvg/UPLOADS-6201---6400/6301-Bharathi_Ramasubban/",
                                "https://www.sangeethamshare.org/tvg/UPLOADS-1801---2000/1914-KS_Narayanaswami-Veena-FM_Amritavarshini/",
                                "https://www.sangeethamshare.org/tvg/UPLOADS-3201---3400/3351-MS_Sheela-Veenai_Kuppiyer_Compositions/",
                                "https://www.sangeethamshare.org/tvg/UPLOADS-3601---3800/3800-S_Saketharaman/"]
                related_table = {
                    "Related Links": [
                        {"Kriti (Song)": 'sarOja daLa nEtri himagiri', "Ragam": 'shankarAbharaNam',
                        "Composer": 'Syama Sastri', "Artist": 'TN Seshagopalan', "Link": related_links[0]},
                        {"Kriti (Song)": 'dakSinNAmUrtE', "Ragam": 'shankarAbharaNam',
                        "Composer": 'Muthuswamy Dikshitar', "Artist": 'Bharathi Ramasubban', "Link": related_links[1]},
                        {"Kriti (Song)": 'manasu svAdhInamaina', "Ragam": 'shankarAbharaNam',
                        "Composer": 'Tyagaraja', "Artist": 'KS Narayanaswami', "Link": related_links[2]},
                        {"Kriti (Song)": 'bAgu mIraganu', "Ragam": 'shankarAbharaNam',
                        "Composer": 'Veenai Kuppiyer', "Artist": 'MS Sheela	', "Link": related_links[3]},
                        {"Kriti (Song)": 'yArenreNNAmalE', "Ragam": 'shankarAbharaNam',
                        "Composer": 'Arunachala Kavi', "Artist": 'S Saketharaman', "Link": related_links[4]}
                    ]
                }
            
            tables[file] = json2html.convert(json=related_table,
                    table_attributes="id=\"link-table\" class=\"table table-bordered table-hover\""
            )
           
        html = render_template('index.html',
                               files=files, js_resources=js_resources,
                               css_resources=css_resources,
                               scripts=scripts,
                               divs=divs,
                               tables=tables)
        return html
    return '', 204


@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)


if __name__ == '__main__':
    app.run(port=33507)