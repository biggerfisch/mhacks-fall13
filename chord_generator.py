from __future__ import division
from pprint import pprint
import json
import random
import os
import timeit
import re
from itertools import cycle, islice
from midiutil.MidiFile import MIDIFile
#THIS SHIT WORKS HOLY SHIT IT WORKS DON'T TOUCH IT. 
#I get list of notes, list of starting times, and list of lengths
print("Loading shit")
ChordDictionary = {}
path = 'data/json-responses/'
for root, dirs, files in os.walk(path):
    for name in files:
        jsondata = open(path + name)
        ChordDictionary[name] = json.load(jsondata)
first_chord_data_path = 'data/first_json'
first_json_data = open(first_chord_data_path)
first_json = json.load(first_json_data)
print("Shit loaded")

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

# def getRoot(ListOfNotes,ListofTimes):
#     print "BAKA"

# def getKey(ListOfNotes,ListofTimes,root):
#     print "BAKA"

def getNumberofMeasures(ListofTimes):
    total = 0
    for i in ListofTimes:
        total = total + i
    return int(total/8) #If total/8 is int

def getNotesInMeasure(ListOfNotes,ListofTimes,MeasureNumber):
    numnotes = 0
    notesInMeasure = []
    BeatPosition = 0
    startOfMeasure = 0
    endOfMeasure = 0
    for beatLength in ListofTimes:
        BeatPosition = BeatPosition + beatLength
        if(BeatPosition <= 8*MeasureNumber):
            startOfMeasure = startOfMeasure + 1
        if(BeatPosition <= 8*MeasureNumber+8):
            endOfMeasure = endOfMeasure + 1
    for noteIndex in range(startOfMeasure,endOfMeasure):
        notesInMeasure.append(ListOfNotes[noteIndex])
    return notesInMeasure

def noteisNotInChord(note,Chord):
    for tone in Chord:
        if tone == note:
            return False
    return True

def noteIsMajorSecond(rootOfChord,note):
    if abs(rootOfChord - note) == 2:
        return True
    return False

def chordFits(Chord,notesInMeasure,root):
    numberofConflicts = 0
    Chord = [note + root for note in Chord]
    for note in notesInMeasure:
        for tone in Chord:
            if noteisNotInChord(note,Chord) and not noteIsMajorSecond(root,note):
                if abs(note - tone) == 1 or abs(note - tone) == 11 or abs(note - tone) == 13 or abs(note - tone) == 23:
                    return False
                if abs(note - tone) == 6 or abs(note - tone) == 18: #or abs(note - tone) == 13 or abs(note - tone) == 23::
                    return False
                if abs(note - tone) == 8 or abs(note - tone) == 4 or abs(note - tone) == 20 or abs(note - tone) == 26:
                    return False
                if abs(note - tone) == 2 or abs(note - tone) == 10:
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
        # pprint(chord)
    assert False, "Shouldn't get here"

def weightedFirstChordChoice(chords):
    total = 0
    for chord in chords:
        total = total + int(chord[0]['prob'])
    r = random.uniform(0, total)
    # print(r)
    # print "155"
    #pprint(chords)
    upto = 0
    for chord in chords:
        if upto + float(chord[0]['prob']) > r:
            return chord
        upto += float(chord[0]['prob'])
    assert False, "Shouldn't get here"

def getFirstChord(notesInMeasure):
    not_shitty_chords = []
    for i in range(12):
        root = 48 + i
        not_shitty_chords += [(j,root) for j in first_json if chordFits(voice_chord(j['path']),notesInMeasure,root)]
    if not_shitty_chords:
        return weightedFirstChordChoice(not_shitty_chords)

def ChordGenerator(ListOfNotes,ListofTimes):
    #List of notes will be between 48 and 64 as constrained by client-side input
    #THIS COMMENT IS IMPORTANT ^^^

    #Generate all possible starting chords
    #Try them in all 12 keys
    #first_json probablities of all starting chords

    #Returns One Chord per measure. Total of 8 eighth notes per measure
    #No key changes in Melody aka one Mode.
    numMeasures = getNumberofMeasures(ListofTimes);
    ListOfChords = [];
    firstChord, root = getFirstChord(getNotesInMeasure(ListOfNotes,ListofTimes,0))
    i = firstChord['path']
    ListOfChords.append(i)
    for numba in range(numMeasures-1):
        num = numba + 1 
        i = i.replace("/","#")
        data = ChordDictionary[i]
        notesInMeasure = getNotesInMeasure(ListOfNotes,ListofTimes,numba);
        tempChord = weightedChordChoice(data['children']) 
        ChordIntoNotes = voice_chord(tempChord['SInED'])   
        
        while(not chordFits(ChordIntoNotes,notesInMeasure,root)):
            tempChord = weightedChordChoice(data['children'])
            ChordIntoNotes = voice_chord(tempChord['SInED'])
        # pprint(tempChord)
        ChordIntoNotes = voice_chord(tempChord['SInED']) 
        # newListToMakeShitMakeSense = [x+1 for x in ChordIntoNotes]
        # print(newListToMakeShitMakeSense)
        ListOfChords.append(tempChord['SInED'])
        i = i + '.' + convertToFilePathSyntax(tempChord['SInED'])

    return [voice_chord(c) for c in ListOfChords],root #One Chord Per Measure

def MidiFileCreator(ListOfRelativeChordVoicings,root,token,bpm):
    MyMIDI = MIDIFile(1)
    track = 0
    channel = 0
    time = 0
    duration = 1
    volume = 100
    MyMIDI.addTrackName(track,time,token)
    MyMIDI.addTempo(track,time,bpm)
    #Sends Chords to MIDI
    for chord in ListOfRelativeChordVoicings:
        for note in chord:
            MyMIDI.addNote(track,channel,int(note),time,duration,volume)
        time = time + 1

    binfile = open(token + ".mid", 'wb')
    MyMIDI.writeFile(binfile)
    binfile.close()
#Testing Area:
ListOfNotes = [48,50,51,50,48,48,50,51,55,50,51,50]
ListofTimes = [1,1,2,2,2,1,1,1,1,1,1,2]
print(ChordGenerator(ListOfNotes,ListofTimes))
