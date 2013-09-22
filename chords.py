from chord_generator import ChordGenerator, MidiFileCreator

from flask import Flask, request, jsonify, render_template, abort, make_response
from pymongo import MongoClient

import random
import base64

app = Flask(__name__)

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
    return render_template('computer-keyboard.html')

@app.route('/playback/')
def playback_page():
    return render_template('play-midifile.html')
    
if __name__ == '__main__':
    app.run(debug=True)
