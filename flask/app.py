from flask import Flask, redirect, url_for, request, render_template, Response, jsonify, redirect
from werkzeug.utils import secure_filename

import os
import sys

import speech_recognition as sr
from os import path

from pydub import AudioSegment
import math

import glob
import time
import librosa
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
import re
from wordcloud import WordCloud
import wave
import contextlib

class SplitWavAudioMubin():
    def __init__(self, folder, filename):
        self.folder = folder
        self.filename = filename
        self.filepath = folder + '\\' + filename

        self.audio = AudioSegment.from_wav(self.filepath)

    def get_duration(self):
        return self.audio.duration_seconds

    def single_split(self, from_min, to_min, split_filename):
        t1 = from_min * 60 * 1000
        t2 = to_min * 60 * 1000
        split_audio = self.audio[t1:t2]
        split_audio.export(self.folder + '\\' + split_filename, format="wav")

    def multiple_split(self, min_per_split):
        total_mins = math.ceil(self.get_duration() / 60)
        for i in range(0, total_mins, min_per_split):
            split_fn = str(i) + '_' + self.filename
            self.single_split(i, i+min_per_split, split_fn)
            print(str(i) + ' Done')
            if i == total_mins - min_per_split:
                print('All splited successfully')

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET'])
def uploader():
    return render_template('upload.html')

@app.route('/audiosaver', methods=['GET'])
def audiosaver():
    return render_template('audiosaver.html')

@app.route('/upload', methods=['POST'])
def my_form_post():
    # requesting the file and folder
    folder = request.form['file_path']
    file = request.form['filename']
    fname = folder + '//' +file
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames/float(rate)

    if duration > 60:
        #spliting audio into one one minute chunks
        split_wav = SplitWavAudioMubin(folder, file)
        split_wav.multiple_split(min_per_split=1)

        #convert each one minute chuck into text and puuting it together
        audio_list = glob.glob(folder+'\\*.wav')
        transcribed_text = ""
        for audioi in range(len(audio_list)-1):
            r = sr.Recognizer()
            with sr.AudioFile(audio_list[audioi]) as source:
                audio = r.record(source)
            try:
                transcribed_text +=  r.recognize_sphinx(audio) + " "
            except sr.UnknownValueError:
                print("Sphinx could not understand audio")
            except sr.RequestError as e:
                print("Sphinx error; {0}".format(e))

        #finding Average word said in one minute
        length = len(list(transcribed_text))
        fname = folder + '//' +file
        with contextlib.closing(wave.open(fname,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames/float(rate)
        audio_words_per_minute = int((length/duration)*60)


        #text preprocessing and generating wordcloud
        text = transcribed_text
        text = re.sub('[^A-Za-z0-9]+', ' ', text)
        text.lower()
        text = set(text.split())
        filler_word = {'well', 'um', 'er', 'uh', 'hmm', 'like', 'actually', 'basically', 'seriously', 'see', 'mean', 'believe', 'guess', 'umm','mhm', 'so'}
        concat_words = text.intersection(filler_word)
        f_text = ""
        for i in concat_words:
            f_text += i
            f_text += " "
        if len(f_text) == 0:
            plotfile1 = None
        else:
            wordcloud = WordCloud().generate(f_text)
            wordcloud = WordCloud(background_color="white",max_words=len(f_text)+10,max_font_size=40, relative_scaling=.5).generate(f_text)
            plt.figure()
            plt.imshow(wordcloud)
            plt.axis("off")
            plt.title('WordCloud of fillwords present in script')
            if not os.path.isdir('static'):
                os.mkdir('static')
            else:
                for filename in glob.glob(os.path.join('static', '*.png')):
                    os.remove(filename)
                plotfile1 = os.path.join('static', str(time.time()) + '.png')
                plt.savefig(plotfile1)

        #Generating energy graph
        samples, sample_rate = librosa.load(folder+'\\'+file, sr=16000)
        timer = np.arange(0, len(samples))/sample_rate
        fig, ax = plt.subplots()
        ax.plot(timer, samples)
        ax.set(xlabel='time', ylabel='amplitude')
        ax.set_title('Energy Graph')
        plotfile2 = os.path.join('static', str(time.time()) + '.png')
        plt.savefig(plotfile2)

        #removing audio chuck
        for i in range(len(audio_list)-1):
            os.remove(audio_list[i])
    else:
        #transcription
        transcribed_text = ""
        r = sr.Recognizer()
        with sr.AudioFile(fname) as source:
            audio = r.record(source)
        try:
            transcribed_text +=  r.recognize_sphinx(audio) + " "
        except sr.UnknownValueError:
            print("Sphinx could not understand audio")
        except sr.RequestError as e:
            print("Sphinx error; {0}".format(e))

        length = len(list(transcribed_text))
        fname = folder + '//' +file
        with contextlib.closing(wave.open(fname,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames/float(rate)
        audio_words_per_minute = int((length/duration)*60)


        #text preprocessing and generating wordcloud
        text = transcribed_text
        text = re.sub('[^A-Za-z0-9]+', ' ', text)
        text.lower()
        text = set(text.split())
        filler_word = {'well', 'um', 'er', 'uh', 'hmm', 'like', 'actually', 'basically', 'seriously', 'see', 'mean', 'believe', 'guess', 'umm','mhm', 'so'}
        concat_words = text.intersection(filler_word)
        f_text = ""
        for i in concat_words:
            f_text += i
            f_text += " "
        if len(f_text) == 0:
            if not os.path.isdir('static'):
                os.mkdir('static')
            else:
                for filename in glob.glob(os.path.join('static', '*.png')):
                    os.remove(filename)
            plotfile1 = None
        else:
            wordcloud = WordCloud().generate(f_text)
            wordcloud = WordCloud(background_color="white",max_words=len(f_text)+10,max_font_size=40, relative_scaling=.5).generate(f_text)
            plt.figure()
            plt.imshow(wordcloud)
            plt.axis("off")
            plt.title('WordCloud of fillwords present in script')
            if not os.path.isdir('static'):
                os.mkdir('static')
            else:
                for filename in glob.glob(os.path.join('static', '*.png')):
                    os.remove(filename)
                plotfile1 = os.path.join('static', str(time.time()) + '.png')
                plt.savefig(plotfile1)

        #Generating energy graph
        samples, sample_rate = librosa.load(folder+'//'+file, sr=16000)
        timer = np.arange(0, len(samples))/sample_rate
        fig, ax = plt.subplots()
        ax.plot(timer, samples)
        ax.set(xlabel='time', ylabel='amplitude')
        ax.set_title('Energy Graph')
        plotfile2 = os.path.join('static', str(time.time()) + '.png')
        plt.savefig(plotfile2)

    #returning all variables
    if plotfile1 == None:
        return render_template('show.html', plotfile2=plotfile2, audio_words_per_minute=audio_words_per_minute, transcribed_text=transcribed_text)
    else:
        return render_template('show.html', plotfile1=plotfile1, plotfile2=plotfile2, audio_words_per_minute=audio_words_per_minute, transcribed_text=transcribed_text)
if __name__ == '__main__':
    try:
        app.run()
    except Exception as e:
        print('{} error occured'.format(e))
