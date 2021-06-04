import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np
import warnings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import RidgeClassifier
import pickle


warnings.filterwarnings("ignore")

from sklearn import preprocessing


def get_ragams_from_labels(joint_labels, df):
    ragams = list(df['Ragam'])
    le = preprocessing.LabelEncoder()
    le.fit(ragams)
    pickle.dump(le, open('le', 'wb'))
    return [le.classes_[int(joint_labels[i])] for i in range(len(joint_labels))]


def onehot_encoding(y):
    label_encoder = LabelEncoder()
    integer_encoded = integer_encoded = label_encoder.fit_transform(np.array(y))
    onehot_encoder = OneHotEncoder(sparse = False)
    integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
    onehot_encoded = onehot_encoder.fit_transform(integer_encoded)
    return onehot_encoded

def reshape_data(df):
    columns = list(df.columns)[:-1]
    X_train, X_test, y_train, y_test = train_test_split(df[columns], 
                                                   df['Ragam'], 
                                                   test_size = 0.2,
                                                   random_state = 0,
                                                   stratify = df['Ragam'])
    X_train_arr = X_train.to_numpy()
    X_test_arr = X_test.to_numpy()
    X_train_arr = X_train_arr.reshape((X_train_arr.shape[0], X_train_arr.shape[1], 1))
    X_test_arr = X_test_arr.reshape((X_test_arr.shape[0], X_test_arr.shape[1], 1))
    y_train_onehot = onehot_encoding(y_train)
    y_test_onehot = onehot_encoding(y_test)
    
    return X_train_arr, X_test_arr, y_train_onehot, y_test_onehot, y_train, y_test

def get_n_class_df(df, ragams):
    class_df = df[df['Ragam'] == ragams[0]]
    for i in range(1, len(ragams)):
        class_df = class_df.append(df[df['Ragam'] == ragams[i]])    
    return class_df

def rf_model_indep_feat(X_train, X_test, y_train, y_test):
    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1])
    X_test = X_test.reshape(X_test.shape[0], X_test.shape[1])
    classifier = RandomForestClassifier(n_estimators = 200, n_jobs = -1)
    cross_val = KFold(n_splits=5)
    scores = cross_val_score(classifier, X_train, y_train,
                             cv=cross_val, scoring='accuracy')
    classifier.fit(X_train, y_train)
    print(scores.mean())
    y_pred = classifier.predict(X_test)

    return classifier, y_pred, y_test

def ridge_model_indep_feat(X_train, X_test, y_train, y_test):
    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1])
    X_test = X_test.reshape(X_test.shape[0], X_test.shape[1])
    classifier = RidgeClassifier()
    cross_val = KFold(n_splits=5)
    scores = cross_val_score(classifier, X_train, y_train,
                             cv=cross_val, scoring='accuracy')
    classifier.fit(X_train, y_train)
    print(scores.mean())
    y_pred = classifier.predict(X_test)

    return classifier, y_pred, y_test


def main():

    features_train = np.genfromtxt('features_train.csv', delimiter=',')
    labels_train = np.genfromtxt('labels_train.csv', delimiter=',')

    df = pd.read_csv('sample_min_rag_100_samp_100_50_df.csv')

    res_df = pd.DataFrame(features_train)
    res_df['Ragam'] = get_ragams_from_labels(labels_train, df)

    sample_ragams = ['kalyANi', 
                    'tODi', 
                    'shankarAbharaNam', 
                    'Anandabhairavi', 
                    'bEgaDA', 
                    'kharaharapriyA', 
                    'bhairavi', 
                    'bilahari', 
                    'shrI', 
                    'kAmbOji',
                    'aThANA',
                    'dhanyAsi',
                    'mAyAmALavagauLa',
                    'kEdAragauLa', 
                    'sAvEri',
                    'sahAna',
                    'nATTakurinji',
                    'kAnaDA',
                    'darbAr',
                    'behAg']


    
    ten_class_df = get_n_class_df(res_df,sample_ragams[:10])
    #twenty_class_df = get_n_class_df(res_df, sample_ragams[:20])
    X_train, X_val, y_train, y_val, y_train_lab, y_val_lab = reshape_data(ten_class_df)


    rf, y_pred, y_val_proc = rf_model_indep_feat(X_train, X_val, y_train, y_val)
    print('Random Forest Accuracy', accuracy_score(y_val_proc, y_pred))
    pickle.dump(rf, open('rf_model', 'wb'))
    #print(classification_report(y_val_proc, y_pred, digits=3))

    ridge, y_pred, y_val_proc = ridge_model_indep_feat(X_train, X_val, y_train_lab, y_val_lab)
    pickle.dump(ridge, open('ridge_model', 'wb'))
    print('Ridge Accuracy', accuracy_score(y_val_proc, y_pred))
