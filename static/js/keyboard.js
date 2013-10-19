window.addEventListener('load', function() {
    // Dirty dirty globals...
    window.noteMap = {
        "gs": 68,
        "a": 69,
        "bb": 70,
        "b": 71,
        "c": 72,
        "cs": 72,
        "d": 73,
        "eb": 74,
        "e": 75,
        "f": 76,
        "fs": 77,
        "g": 78
    };

    window.noteStarts = [];
    window.noteStops = [];

    Piano.load("piano", {
        width: 550,
        height: 550,
        backgroundFill: "#333",
        onKeyPress: function(note){
            console.log(note + " pressed");
            window.noteStarts.push([window.noteMap[note], Date.now()]);
        },
        onKeyRelease: function(note){
            console.log(note + " released");
            window.noteStops.push([window.noteMap[note], Date.now()])
        }
    });
});

function closestMultiple(n, b) {
    var closest = 1;
    var current = 1;
    while (current * (b-1) < n) {
        if (Math.abs(current * b - n) < Math.abs(closest * b - n)) {
            closest = current;
        }
        current += 1;
    }
    return closest;
}

function toTimeSig(b) {
    // If the Shu fits... :)
    return String(Math.floor(b / 4)) + "." + String(b % 4 + 1);
}

function toBeat(ts) {
    s = ts.split('.');
    return Number(s[0]) * 4 + Number(s[1]);
}

function displayTune(pitchList, timeList){
    console.log("displayTune");
    console.log(pitchList.length);
    var NUM_MEASURES = 4; // Hard coded for now

    for (var i = 0; i < pitchList.length; i++) {
        var beat = toBeat(timeList[i]);
        console.log(beat);
        if (beat < NUM_MEASURES * 4) {
            console.log("#c-" + (pitchList[i] - 68) + "-" + beat);
            var checkbox = $("#c-" + (pitchList[i] - 68) + "-" + beat);
            checkbox.prop('checked', true);
        }
    }
}

function sendData(bpm, pitchList, timeList, durationList){
    if (pitchList.length == 0){
        return;
    }
    d = {
        bpm: bpm,
        pitches: pitchList,
        times: timeList,
        durations: durationList
    }
    jQuery.ajax({
        type: "POST",
        url: "http://" + window.location.host + "/songs",
        contentType: 'application/json',
        data: JSON.stringify(d),
        dataType: "json",
        success: function(response){
            console.log(JSON.stringify(response));
            $("#song").val(
                "http://" + window.location.host +
                "/songs/" + response.token
            );
        }
    });
}

function dumpData() {
    var tempo = Number(document.getElementById('tempo').value);
    console.log(tempo);

    var midi_pitches = [];
    var midi_times = [];
    var midi_durations = [];

    var ms_per_eighth = 60000 / tempo / 2;
    
    // Assuming they're the same length for now...
    console.log(window.noteStarts.length, window.noteStops.length);

    var beat = 0;
    for (var i=0; i < window.noteStarts.length; i++) {
        var delta;
        var duration;
        if (window.noteStarts.length === 1) {
            duration = 1;
        } else if (i < window.noteStarts.length - 1) {
            delta = window.noteStarts[i+1][1] - window.noteStarts[i][1];
            duration = closestMultiple(delta, ms_per_eighth);
        } else {
            duration = midi_durations[midi_durations.length-1];
        }

        midi_pitches.push(window.noteStarts[i][0]);
        midi_times.push(toTimeSig(beat));
        midi_durations.push(duration);

        beat += duration;
    }
    console.log(JSON.stringify(midi_pitches));
    console.log(JSON.stringify(midi_times));
    console.log(JSON.stringify(midi_durations));

    displayTune(midi_pitches, midi_times);
    sendData(tempo, midi_pitches, midi_times, midi_durations);
}

function clearData() {
    window.noteStarts = [];
    window.noteStops = [];
    $(".note").prop('checked', false);
}
