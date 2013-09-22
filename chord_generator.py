from __future__ import division
from pprint import pprint
import json
import random
import os
import timeit
import re
from itertools import cycle, islice
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
    # while(BeatPosition<(8*(MeasureNumber+1))+7):
    #     BeatPosition = BeatPosition + ListofTimes[startIndex]
    #     if BeatPosition<8*(MeasureNumber+1):
    #         startOfMeasure= startOfMeasure + 1
    #         print(startIndex)
    #     endOfMeasure = endOfMeasure + 1
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
    for note in notesInMeasure:
        for tone in Chord:
            if noteisNotInChord(note,Chord) and not noteIsMajorSecond(root,note):
                print("AM I REACHING 129?")
                if abs(note - tone) == 1 or abs(note - tone) == 11:
                    return False
                if abs(note - tone) == 6:
                    return False
                if abs(note - tone) == 8 or abs(note - tone) == 4:
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
    total = 100;
    # for chord in chords:
    #     total = total + int(chord['prob'])
    r = random.uniform(0, total)
    # print(r)
    # print "155"
    #pprint(chords)
    upto = 0
    for chord in chords:
        # print(100*float(chord['prob']))
        if upto + 100*float(chord['prob']) > r:
            print(chord)
            return chord
        upto += 100*float(chord['prob'])
    assert False, "Shouldn't get here"


# def convertChordToNoteList(Chord,rootOfSong,mode):
#     ChordNoteList = []
#     #Use Charlie's shit here
#     chordNumber = Chord['SInED']

#     return chord(mode,)

def getFirstChord(notesInMeasure):
    first_chord_data_path = '/Users/vikas/Documents/Mhacks-Fall13/mhacks-fall13/data/first_json'
    first_json_data = open(first_chord_data_path)
    first_json = json.load(first_json_data)
    listofPossibleChords = []
    outputChordList = []
    for i in range(12):
        root = 48 + i #(i+random.randrange(0,11))%12
        print (root)
        bakaChord = weightedFirstChordChoice(first_json)
        tries = 0
        print(chordFits(voice_chord(bakaChord['path']),notesInMeasure,root))
        while(not chordFits(voice_chord(bakaChord['path']),notesInMeasure,root) or tries > 40):
            bakaChord = weightedFirstChordChoice(first_json)
            tries = tries + 1
            print ("trying again")
            print(chordFits(voice_chord(bakaChord['path']),notesInMeasure,root))
        if tries <= 40:
            notesInChordList = voice_chord(bakaChord['path'])
            chordMadeInAllKeys = [x+root for x in notesInChordList]
            return chordMadeInAllKeys, root, bakaChord['path']
        # pprint(x for x in chordMadeInAllKeys)

    return outputChord, root

def ChordGenerator(ListOfNotes,ListofTimes):
    #Generate all possible starting chords
    #Try them in all 12 keys
    #first_json probablities of all starting chords

    #Returns One Chord per measure. Total of 8 eighth notes per measure
    #No key changes in Melody aka one Mode.
    ChordDictionary = {}
    path = '/Users/vikas/Documents/Mhacks-Fall13/mhacks-fall13/data/json-responses/'
    for root, dirs, files in os.walk(path):
        for name in files:
            jsondata = open(path + name)
            ChordDictionary[name] = json.load(jsondata)
    # mode = aeolian
     #getKey(ListOfNotes,ListofTimes,root) #Gets mode from notes
    #listofPossibleChords = getListOfChords(mode) #Generates chords from mode

    numMeasures = getNumberofMeasures(ListofTimes);
    ListOfChords = [];
    (firstChord,root, i) = getFirstChord(getNotesInMeasure(ListOfNotes,ListofTimes,0))
    ListOfChords.append(i)
    print (firstChord)
    # pprint(firstChord) #This is the Parent
    #JsonResponseslocation = '/Users/vikas/Documents/Mhacks-Fall13/mhacks-fall13/data/json-responses/'
    #You Baka, make this relative path shit.
    for numba in range(numMeasures-1):
        num = numba + 1 
        i = i.replace("/","#")
        data = ChordDictionary[i]
        notesInMeasure = getNotesInMeasure(ListOfNotes,ListofTimes,numba);
        tempChord = weightedChordChoice(data['children']) 
        ChordIntoNotes = voice_chord(tempChord['SInED'])   
        
        while(not chordFits(ChordIntoNotes,notesInMeasure,root)):
            tempChord = weightedChordChoice(data['children'])
        # pprint(tempChord)
        ChordIntoNotes = voice_chord(tempChord['SInED']) 
        # newListToMakeShitMakeSense = [x+1 for x in ChordIntoNotes]
        # print(newListToMakeShitMakeSense)
        ListOfChords.append(tempChord['SInED'])
        i = i + '.' + convertToFilePathSyntax(tempChord['SInED'])

    return ListOfChords,root #One Chord Per Measure

#main shit:
# ChordDictionary = {}
# path = '/Users/vikas/Documents/Mhacks-Fall13/mhacks-fall13/data/json-responses/'
# for root, dirs, files in os.walk(path):
#     for name in files:
#         jsondata = open(path + name)
#         ChordDictionary[name] = json.load(jsondata)
# #print(ChordDictionary[i])
ListOfNotes = [60,62,63,62,60,60,62,63,67,62,63,60]
ListOfNotes = [note - 11 for note in ListOfNotes]
pprint(ListOfNotes)
ListofTimes = [1,1,2,2,2,1,1,1,1,1,1,2]
# #pprint(getNumberofMeasures(ListofTimes))
# #ChordGenerator(ListOfNotes,ListofTimes)
# numMeasures = getNumberofMeasures(ListofTimes);
# ListOfChords = [];
# i = '6' #str(getFirstChord(getNotesInMeasure(ListOfNotes,ListofTimes,0),mode))
# firstChord = ChordDictionary[i]['parent']
# #pprint(firstChord)
# #JsonResponseslocation = '/Users/vikas/Documents/Mhacks-Fall13/mhacks-fall13/data/json-responses/'
# #You Baka, make this relative path shit.
# for numba in range(numMeasures-1):
#     num = numba + 1 
#     data = ChordDictionary[i]
#     notesInMeasure = getNotesInMeasure(ListOfNotes,ListofTimes,num);
#     tempChord = weightedChordChoice(data['children'])    
#     while(not chordFits(voice_chord(tempChord['SInED']),notesInMeasure)):
#         tempChord = weightedChordChoice(data['children'])
#     #pprint(tempChord)
#     print(voice_chord(tempChord['SInED']))
#     ListOfChords.append(tempChord)
#     i = i + '.' + convertToFilePathSyntax(tempChord['SInED'])
print(ChordGenerator(ListOfNotes,ListofTimes))


