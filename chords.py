from flask import Flask, request, jsonify, render_template, abort, make_response
from pymongo import MongoClient
from chord_generator import ChordGenerator

import random
import base64
import logging

app = Flask(__name__)
file_handler = logging.FileHandler(filename='/tmp/chordinator.log')
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

app.logger.debug("Testing one two three")

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
    return render_template('home.html')

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
    times = [4*int(l)+int(r) - 1 for p in pairs]
    intervals = [l-r for l,r in zip(times[1:],times)] + [1]

    chords, center = ChordGenerator(request.json['pitches'], intervals)
    song = {
            'token': token,
            'chord_pitches': chords,
            'chord_times': [4]*len(chords),
            'chord_center': center
    }
    db.songs.insert(song)

    MidiFileCreator(token)

    return jsonify({'token': token}), 201

@app.route('/songs/<token>')
def fetch_song(token):
    melody = db.melodies.find_one({'token': token})
    song = db.songs.find_one({'token': token})
    if song:
        return jsonify({'notes': song['notes']})
    else:
        abort(404)

@app.route('/about/')
def about_page():
    return render_template('about.html')

@app.route('/keyboard/')
def keyboard_page():
    return render_template('computer-keyboard.html')

@app.route('/playback/')
def playback_page():
    return render_template('play-midifile.html')
    
if __name__ == '__main__':
    app.run(debug=True)
