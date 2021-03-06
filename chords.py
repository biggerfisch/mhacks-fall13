from chord_generator import ChordGenerator, MidiFileCreator, synthesize_wav

from flask import Flask, request, jsonify, render_template, abort, make_response
from pymongo import MongoClient

import random
import base64

import logging
import os

app = Flask(__name__)
app.config.from_pyfile('app.cfg')

#if app.debug is not True:
if True:
    file_handler = logging.FileHandler(os.path.join('/tmp','python.log'))
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)

@app.errorhandler(500)
def internal_error(exception):
    app.logger.exception(exception)
    return render_template('500.html'), 500

client = MongoClient()
db = client['chordinator']

def rand_token():
    token = base64.urlsafe_b64encode(str(random.randint(1000,1000000)))
    while db.melodies.find_one({'token': token}):
        token = base64.urlsafe_b64encode(str(random.randint(1000,1000000)))
    return token

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error':'Not found'}),404)

@app.route('/')
def home_page():
    #return render_template('home.html')
    return render_template('computer-keyboard.html')

@app.route('/songs', methods = ['POST'])
def make_song():
    
    if not request.json:
        abort(400)
    token = rand_token()
    melody = {
            'token': token,
            'bpm': request.json['bpm'],
            'pitches': request.json['pitches'],
            'times': request.json['times'],
            'durations': request.json['durations']
    }
    db.melodies.insert(melody)

    pairs = [t.split('.') for t in request.json['times']]
    times = [4*int(l)+int(r) - 1 for l,r in pairs]
    
    pitches = [int(p) for p in request.json['pitches']]
    durations = [int(d) for d in request.json['durations']]
    
    chords, center = ChordGenerator(pitches, durations, times)
    
    song = {
            'token': token,
            'chord_pitches': chords,
            'chord_times': [4]*len(chords),
            'chord_center': center
    }
    db.songs.insert(song)
    
    dbMelody = db.melodies.find_one({'token': token})
    dbSong = db.songs.find_one({'token': token})
    
    MidiFileCreator(dbMelody,dbSong)
    synthesize_wav(token)

    return jsonify({'token': token,
    'chords': chords}), 201

@app.route('/songs/<token>')
def fetch_song(token=None):
    song = db.melodies.find({'token': token})
    if song:
        #return jsonify({'notes': song['notes']})
        return render_template('song.html', token=token)
    else:
        abort(404)

@app.route('/about/')
def about_page():
    return render_template('about.html')

@app.route('/keyboard/')
def keyboard_page():
    return render_template('noteboard.html')

@app.route('/playback/')
def playback_page():
    return render_template('play-midifile.html')
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
