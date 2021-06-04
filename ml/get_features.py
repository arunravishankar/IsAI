import pandas as pd
from datetime import datetime
import numpy as np
import os
import librosa
from sklearn.model_selection import train_test_split


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

def parse_audio_files(indices, ragams, le):
    begin_time = datetime.now()
    features, labels = np.empty((0,193)), np.empty(0) # 193 => total features
    workdir = os.path.join(os.getcwd(), 'songs')
    j = 0
    begin_time = datetime.now()
    for index, ragam in zip(indices, ragams):
        if j%50==0:
            print(j, datetime.now().strftime("%H:%M:%S"))
        j+=1
        filename = os.path.join(workdir, 'song_{}.mp3'.format(index)) 
        try:
            for i in range(50):
                mfccs, chroma, mel, contrast, tonnetz = extract_feature(filename, i)
                ext_features = np.hstack([mfccs, chroma, mel, contrast, tonnetz])
                features = np.vstack([features, ext_features])
                ragam_e = le.transform([ragam])[0]
                labels = np.append(labels, ragam_e)
        except:
            continue
    print(datetime.now()-begin_time)
    return np.array(features, dtype=np.float32), np.array(labels, dtype = np.int8)


