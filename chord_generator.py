def ChordGenerator(ListOfNotes,ListofTimes):
	#Returns One Chord per measure. Total of 8 eighth notes per measure
	#No key changes in Melody aka one Mode.
	mode = getModeTonality(ListOfNotes,ListofTimes) #Gets mode from notes
	listofPossibleChords = getListOfChords(mode) #Generates chords from mode
	for i in ListOfNotes:
		
	return ListOfChords #One Chord Per Measure

