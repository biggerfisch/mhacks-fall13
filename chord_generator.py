from __future__ import division

from flask import Flask

import json
import random
import os
import timeit
import re
from itertools import cycle, islice
from midiutil.MidiFile import MIDIFile
import subprocess

app = Flask(__name__)
app.config.from_pyfile('app.cfg')

ChordDictionary = {}
first_json = {}
base = app.config['BASE_PATH']
path = base + 'data/json-responses/'
for root, dirs, files in os.walk(path):
    for name in files:
        jsondata = open(path + name)
        ChordDictionary[name] = json.load(jsondata)
first_chord_data_path = base + 'data/first_json'
first_json_data = open(first_chord_data_path)
first_json = json.load(first_json_data)
def sum_n(series, n):
    return sum(islice(series,0,n))

def scale(intervals):
    def this_scale(degree):
        deg = degree - 1
        if not deg < 0:
            return sum_n(cycle(intervals), deg)
        else:
            deg2 = -deg + 1
            return - (scale(list(reversed(intervals))))(deg2)
    return this_scale

major = scale([2,2,1,2,2,2,1])

def shift_mode(mode, steps):
    def shifted(deg):
        return mode(steps + deg) - mode(steps + 1)
    return shifted

locrian    = shift_mode(major, -1)
aeolian    = shift_mode(major, -2)
mixolydian = shift_mode(major, -3)
lydian     = shift_mode(major, -4)
phrygian   = shift_mode(major, -5)
dorian     = shift_mode(major, -6)

def chord(mode, root, intervals):
    return [root - 1 + mode(i) for i in intervals]
def triad(mode,root):
    return chord(mode,root,[1,3,5])
def invert_6(mode,root):
    return chord(mode,root,[3,5,8])
def invert_6_4(mode,root):
    return chord(mode,root,[5,8,10])
def with_7(mode,root):
    return chord(mode,root,[1,3,5,7])
def slash_chord(left, right):
    c = voice_chord(left)
    return [x + major(int(right)) for x in c]
def voice_chord(url):
    if url[0] == 'b':
        mode = aeolian
    elif url[0] == 'M':
        mode = mixolydian
    elif url[0] == 'L':
        mode = lydian
    elif url[0] == 'C':
        mode = locrian
    elif url[0] == 'Y':
        mode = phrygian
    elif url[0] == 'D':
        mode = dorian
    else:
        mode = major
    
    slash_match = re.compile(r'(.*)/(\d)$').match(url)
    if slash_match:
        return slash_chord(slash_match.group(1), slash_match.group(2))
    
    chords = [(r'(\d)$', triad),
            (r'(\d)6$', invert_6),
            (r'(\d)64$', invert_6_4),
            (r'(\d)7$', with_7)]
    for r, f in chords:
        match = re.compile(r).search(url)
        if match:
            return f(mode, int(match.group(1)))
def chord_in_key(url,root):
    listofNotes = voice_chord(url)
    listofNotes = [note + root for note in listofNotes]
def convertToFilePathSyntax(ChordNameString):
    ChordNameString = ChordNameString.replace('/','#')
    return ChordNameString

def getNumberofMeasures(ListofTimes):
    # total = 0
    # for i in ListofTimes:
    #     total = total + i
    # return int(total/8) #If total/8 is int
    return ListofTimes[-1]/4

def getNotesInMeasure(ListOfNotes,ListofTimes,MeasureNumber):
    notesInMeasure = []
    StartBeatPosition = 4*MeasureNumber   
    for i in range(StartBeatPosition,StartBeatPosition+3):
        for times in ListofTimes:            
            if i == times:
                notesInMeasure.append(ListOfNotes[ListofTimes.index(times)])
    return notesInMeasure
    # for beatLength in ListofTimes:
    #     BeatPosition = BeatPosition + beatLength
    #     if(BeatPosition <= 4*MeasureNumber):
    #         startOfMeasure = startOfMeasure + 1
    #     if(BeatPosition <= 4*MeasureNumber+4):
    #         endOfMeasure = endOfMeasure + 1
    # for noteIndex in range(startOfMeasure,endOfMeasure):
    #     notesInMeasure.append(ListOfNotes[noteIndex])

def noteisNotInChord(note,Chord):
    for tone in Chord:
        if tone == note: #or tone - note - 12 == 0 or note - tone - 12 == 0:
            return False
    return True

def noteIsMajorSecond(rootOfChord,note):
    if abs(rootOfChord - note) == 2:
        return True
    return False

def chordFits(Chord,notesInMeasure,root):
    numberofConflicts = 0
    NewChord = []
    for note in Chord:
        NewChord.append(note+root)
    Chord = NewChord
    for note in notesInMeasure:
        for tone in Chord:
            if noteisNotInChord(note,Chord) and not noteIsMajorSecond(root,note):
                if abs(note - tone) == 1 or abs(note - tone) == 11 or abs(note - tone) == 13 or abs(note - tone) == 23:
                    return False
                if abs(note - tone) == 6 or abs(note - tone) == 18: #or abs(note - tone) == 13 or abs(note - tone) == 23::
                    return False
                if abs(note - tone) == 8 or abs(note - tone) == 4 or abs(note - tone) == 20 or abs(note - tone) == 26:
                    return False
                if abs(note - tone) == 2 or abs(note - tone) == 10 or abs(note - tone) == 14 or abs(note - tone) == 22:
                    numberofConflicts = numberofConflicts + 1
    if(numberofConflicts > 3):
        return False
    return True

def weightedChordChoice(chords):
    total = 0;
    for chord in chords:
        total = total + int(chord['count'])
    r = random.uniform(0, total)
    upto = 0
    for chord in chords:
        if upto + int(chord['count']) > r:
            return chord
        upto += int(chord['count'])
    assert False, "Shouldn't get here"

def weightedFirstChordChoice(chords):
    total = 0
    for chord in chords:
        total = total + int(chord[0]['prob'])
    r = random.uniform(0, total)
    upto = 0
    for chord in chords:
        if upto + float(chord[0]['prob']) > r:
            return chord
        upto += float(chord[0]['prob'])
    assert False, "Shouldn't get here"

def getFirstChord(notesInMeasure):
    not_shitty_chords = []
    for i in range(12):
        root = 68 + i
        not_shitty_chords += [(j,root) for j in first_json if chordFits(voice_chord(j['path']),notesInMeasure,root)]
    if not_shitty_chords:
        return weightedFirstChordChoice(not_shitty_chords)
    else:
        return weightedFirstChordChoice([(j,68+i) for i in range(12) for j in first_json])



def ChordGenerator(ListOfNotes,ListofDurations,ListofTimes):
    #List of notes will be between 68 and 78 as constrained by client-side input
    #THIS COMMENT IS IMPORTANT ^^^

    #Generate all possible starting chords
    #Try them in all 12 keys
    #first_json probablities of all starting chords

    #Returns One Chord per measure. Total of 8 eighth notes per measure
    #No key changes in Melody aka one Mode.
    
    #abort(401)
    
    numMeasures = getNumberofMeasures(ListofTimes);
    ListOfChords = [];
    firstChord, root = getFirstChord(getNotesInMeasure(ListOfNotes,ListofTimes,0))
    i = firstChord['path']
    ListOfChords.append(i)
    for numba in range(int(numMeasures)-1):
        num = numba + 1 
        i = i.replace("/","#")
        if i not in ChordDictionary:
            break
        data = ChordDictionary[i]
        notesInMeasure = getNotesInMeasure(ListOfNotes,ListofTimes,numba);
        tempChord = weightedChordChoice(data['children']) 
        ChordIntoNotes = voice_chord(tempChord['SInED'])   
        
        while(not chordFits(ChordIntoNotes,notesInMeasure,root)):
            tempChord = weightedChordChoice(data['children'])
            ChordIntoNotes = voice_chord(tempChord['SInED'])
        ChordIntoNotes = voice_chord(tempChord['SInED']) 
        # newListToMakeShitMakeSense = [x+1 for x in ChordIntoNotes]
        ListOfChords.append(tempChord['SInED'])
        i = i + '.' + convertToFilePathSyntax(tempChord['SInED'])

    return [voice_chord(c) for c in ListOfChords],root #One Chord Per Measure

def MidiFileCreator(melody,song):  
    bpm = melody['bpm']
    pitches = melody['pitches']
    parts = [t.split('.') for t in melody['times']]
    times = [4*int(l)+int(r)-1 for l,r in parts]
    durations = melody['durations']
    chord_pitches = song['chord_pitches']
    chord_times = song['chord_times']
    chord_center = song['chord_center']
    ListOfRelativeChordVoicings = song['chord_pitches']
    token = melody['token']
    MyMIDI = MIDIFile(1)
    track = 0
    channel = 0
    time = 0
    duration = 4
    volume = 100
    MyMIDI.addTrackName(track,time,"Herp derp")
    MyMIDI.addTempo(track,time,bpm)
    #Sends Chords to MIDI
    root = int(chord_center)
    for chord in ListOfRelativeChordVoicings:
        for note in chord:
            Intnote = int(note + root)
            MyMIDI.addNote(track,channel,Intnote,time,duration,volume)
        time = time + 4   
    for note,time in zip(pitches,times):
        MyMIDI.addNote(track,channel,int(note),int(time),1,volume)
    binfile = open(base + "static/songs/" + token + ".mid", 'wb')
    MyMIDI.writeFile(binfile)
    binfile.close()
    return "blah"

def synthesize_wav(token):
    mid_file = os.path.join(base, "static", "songs", token + ".mid")
    out_file = os.path.join(base, "static", "songs", token + ".wav")
    sf2_file = os.path.join(base, "static", "songs", "piano.sf2")

    subprocess.call(['fluidsynth', '-T', 'wav',
        '-F', out_file, '-ni', sf2_file, mid_file])
