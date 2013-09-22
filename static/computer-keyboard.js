/*!
 *  copyright 2012 abudaan http://abumarkub.net
 *  code licensed under MIT 
 *  http://abumarkub.net/midibridge/license
 * 
 * 
 *  example of how you use your regular computer keyboard to play a MIDI instrument
 * 
 *  dependecies:
 *  - MIDIBridge.js
 *  - MIDIDeviceSelector.js
 * 
 */

// My addition:
var timeDistinction,    // Helps distinguish which metronome beat we are aligned with. should be (60/bpm)*1000/2
noteOnTime,             // The timestamp when noteOn occurred
noteOffTime,            // The timestamp when noteOff occurred
tickTime,               // The timestamp when the metronome tick happened
messages,
metroTick,
globalTempo,
noteOnMeasure,
noteOffMeasure,
noteOnTick,
noteOffTick,
metronomePlaying = false,
metroMeasure = -1,      // THe current measure. Starts at -1 and is added to in the beginning
compensation = 0,       // Delay compensation in ms
distinctFactor = 1;     // Value between (0 and 1).
notesList = new Array(),
startList = new Array(),
lengthList = new Array();

function SendData(){
    if (notesList.length == 0){
        alert("You have not recorded anything! To start recording, press the record button.");
    }
    d = {
        bpm: globalTempo,
        pitches: notesList,
        times: startList,
        durations: lengthList
    }
    jQuery.ajax({
        type: "POST",
        url: "http://biggerfisch.us.to/songs",
        contentType: 'application/json',
        data: JSON.stringify(d),
        dataType: "json",
        success: function(response){
            console.log(JSON.stringify(response));
            window.location = url + "/" + response[token];
        }
    });
}

function clearAll(){
    notesList.length = [];
    startList.length = [];
    lengthList.length = [];
    messages.innerHTML = "";
}

function dispDataClick(){
    for (var i = 0; i < notesList.length; ++i) {
        messages.innerHTML += notesList[i] + ",";
    };
    messages.innerHTML += "<br/>";
    for (var i = 0; i < startList.length; ++i) {
    messages.innerHTML += startList[i] + ",";
    };
    messages.innerHTML += "<br/>";
    for (var i = 0; i < lengthList.length; ++i) {
    messages.innerHTML += lengthList[i] + ",";
    };
}

window.addEventListener('load', function() {

    if(midiBridge.userAgent === "msie8/win"){
        //midiBridge.wrapElement(document);
        document.body.innerHTML = "This example has not yet support for Internet Explorer 8";
        return;
    }

    messages = document.getElementById("messages");

    var midiAccess,
    output,
    outputs = null,
    msgSelectOutput = "<br/><br/><div>Please select a MIDI output...</div>",
    msgKeyMapping = "<span class='keys'>A,S,D,F,G,H,J,K,L</span> are white keys<br/><span class='keys'>W,E,T,Y,U,O,P</span> are black keys<br/><span class='keys'>spacebar</span> is the sustain pedal",
    keysPressed = {},
    selectOutput = document.getElementById("outputs"),
    messageDiv = document.getElementById("help-message");
    
    window.performance = window.performance || {};
    performance.now = (function() {
      return performance.now       ||
             performance.mozNow    ||
             performance.msNow     ||
             performance.oNow      ||
             performance.webkitNow ||
             function() { return new Date().getTime(); };
    })();
        
    function connectKeyboard(){

        var noteNumbers = {
            //white keys
            65 : 48, //key a -> note c
            83 : 50, //key s -> note d
            68 : 52, //key d -> note e
            70 : 53, //key f -> note f
            71 : 55, //key g -> note g
            72 : 57, //key h -> note a
            74 : 59, //key j -> note b
            75 : 60, //key k -> note c
            76 : 62, //key l -> note d
            186 : 64, //key ; -> note e
            222 : 65, //key : -> note f
            //black keys
            87 : 49, //key w -> note c#/d♭
            69 : 51, //key e -> note d#/e♭
            84 : 54, //key t -> note f#/g♭
            89 : 56, //key y -> note g#/a♭
            85 : 58, //key u -> note a#/b♭
            79 : 61, //key o -> note c#/d♭
            80 : 63  //key p -> note d#/e♭
        }
        
        document.addEventListener("keydown", function(e) {
            console.log(e, e.which, e.which.toString(), noteNumbers[e.which.toString()]);
            if(!output){
                return;
            }
            if(e.which === 32) {//spacebar acts as sustain pedal
                output.sendMIDIMessage(midiAccess.createMIDIMessage(midiBridge.CONTROL_CHANGE, 1, 64, 127));
            } else if(noteNumbers[e.which] && !keysPressed[e.which]) {
                // MY ADDITION
                noteOnTime = performance.now();
                getRelevantMidiData(midiBridge.NOTE_ON, noteNumbers[e.which], noteOnTime);
                noteOnMessage = midiAccess.createMIDIMessage(midiBridge.NOTE_ON, 1, noteNumbers[e.which], 100);
                output.sendMIDIMessage(noteOnMessage);
                keysPressed[e.which] = true;
                //messages.innerHTML += noteNumbers[e.which] + "NoteOnTime:" + noteOnTime + "TickTime:" + tickTime + "<br/>";
            }
        }, false);
    
        document.addEventListener("keyup", function(e) {
            if(!output){
                return;
            }
            if(e.which === 32) {
                output.sendMIDIMessage(midiAccess.createMIDIMessage(midiBridge.CONTROL_CHANGE, 1, 64, 0));
            } else if(noteNumbers[e.which]) {
                // MY ADDITION
                noteOffTime = performance.now();
                getRelevantMidiData(midiBridge.NOTE_OFF, noteNumbers[e.which], noteOffTime);
                noteOffMessage = midiAccess.createMIDIMessage(midiBridge.NOTE_OFF, 1, noteNumbers[e.which], 0);
                output.sendMIDIMessage(noteOffMessage);
                keysPressed[e.which] = false;
                //messages.innerHTML += noteNumbers[e.which] + "NoteOffTime:" + noteOffTime + "<br/>";
            }
        }, false);
        
        messageDiv.innerHTML = msgSelectOutput;
    }

    midiBridge.init(function(_midiAccess){
        
        midiAccess = _midiAccess;
        outputs = midiAccess.enumerateOutputs();

        output = midiAccess.getOutput(midiAccess.enumerateOutputs()[0]);

        //messageDiv.innerHTML = "<br/><br/><br/><span class='device-type'>connected: </span><div>" + output.deviceName + "</div>";
        messageDiv.innerHTML = msgKeyMapping;

        /*
        //create dropdown menu for MIDI outputs and add an event listener to the change event
        midiBridge.createMIDIDeviceSelector(selectOutput,outputs,"ouput",function(deviceId){
            
            if(output){
                output.close();
            }
            output = midiAccess.getOutput(outputs[deviceId]);
            
            if(deviceId == -1){
                messageDiv.innerHTML = msgSelectOutput;
            }else{
                //messageDiv.innerHTML = "<br/><br/><br/><span class='device-type'>connected: </span><div>" + output.deviceName + "</div>";
                messageDiv.innerHTML = msgKeyMapping;
            }
        });
        */
        
        connectKeyboard();
    });

    // GETS DATA REGARDING IMPORTANT PARTS OF MIDI MESSAGE. 
    function getRelevantMidiData(midiMessageType, noteVal, noteTimeStamp){
        if (!metronomePlaying){
            return;
        }
        matchToMetronome(midiMessageType, noteTimeStamp);
        if (midiMessageType == midiBridge.NOTE_ON)
        {
            notesList.push(noteVal);
            if (lengthList.length != startList.length){
                var currTotalPos = noteOnMeasure * 4 + noteOnTick;
                var prevTotalSplit = startList[startList.length - 1].split('.');
                var prevTotalPos = parseInt(prevTotalSplit[0]) * 4 + parseInt(prevTotalSplit[1]);
                var oldLen = currTotalPos - prevTotalPos;
                lengthList.push(oldLen);
            }
            startList.push(noteOnMeasure + "." + noteOnTick);
        }
        else if (midiMessageType == midiBridge.NOTE_OFF)
        {
            // THe note off must be the same as the latest note played
            if (notesList[notesList.length - 1] == noteVal){
                var currTotalPos = noteOffMeasure * 4 + noteOffTick;
                var prevTotalPos = noteOnMeasure * 4 + noteOnTick;
                // var prevTotalSplit = startList[startList.length - 1].split('.');
                // var prevTotalPos = parseInt(prevTotalSplit[0]) * 4 + parseInt(prevTotalSplit[1]);
                var oldLen = currTotalPos - prevTotalPos;
                lengthList.push(oldLen);
            }
        }
    }

    // Matches the current note timestamp played to a metronome tick
    function matchToMetronome(midiMessageType, noteTimeStamp){
        var step = (60 / tempo) * 1000;
        // Closer to current tick
        if (Math.abs(tickTime + step - noteTimeStamp) > Math.abs(tickTime - noteTimeStamp))
        {
            // messages.innerHTML += metroTick + "<br/>";
            // messages.innerHTML += "gOT HERE" + "<br/>";
        }
        else    // Next tick otherwise
        {
            if (midiMessageType == midiBridge.NOTE_ON)
            {
                noteOnMeasure = metroMeasure;
                noteOnTick = metroTick;
                if (noteOnTick == 4)
                {
                    noteOnMeasure += 1;
                    noteOnTick = 1;
                }
                else
                {
                    noteOnTick += 1;
                }
                messages.innerHTML += noteOnMeasure + "_" + noteOnTick + "::";
            }
            else if (midiMessageType == midiBridge.NOTE_OFF)
            {
                noteOffMeasure = metroMeasure;
                noteOffTick = metroTick;
                if (noteOffTick == 4)
                {
                    noteOffMeasure += 1;
                    noteOffTick = 1;
                }
                else
                {
                    noteOffTick += 1;
                }
                messages.innerHTML += noteOffMeasure + "_" + noteOffTick + "<br/>";
            }
        }
    }

}, false);

// the metronome!!!
var metronome = function(opts) {
    //primary variables
    var l = typeof opts.len !== "undefined" ? opts.len : 200, // length of metronome arm
        r = typeof opts.angle !== "undefined" ? opts.angle : 20, //max angle from upright 
        w = 2 * l * Math.cos(r),
        tick_func = typeof opts.tick !== "undefined" ? opts.tick : function() {}, //function to call with each tick
        end_func = typeof opts.complete !== "undefined" ? opts.complete : function() {}, //function to call on completion
        playSound = typeof opts.sound !== "undefined" ? opts.sound : true; 

    // initialize Raphael paper if need be        
    switch(typeof opts.paper) {
        case "string": paper = Raphael(opts.paper, w, l + 20); break;
        case "undefined": paper = Raphael(0, 0, w, l + 20); break;
    }

    // initialize audio if need be
    if (playSound && opts.audio) {
        // initialize audio
        var sound = document.createElement('audio');
        sound.setAttribute('src', opts.audio);
        sound.setAttribute('id', 'tick');
        document.body.appendChild(sound);
    }
    
    // derivative variables
    var y0 = l * Math.cos(Math.PI * r / 180),
        x0 = l * Math.sin(Math.PI * r / 180),    
        y = l + 10,
        x = x0 + 10,    
        tick_count = 0;
    
    var outline = paper.path("M"+x+","+y+"l-"+x0+",-"+y0+"a"+l+","+l+" "+2*r+" 0,1 "+2*x0+",0L"+x+","+y).attr({
        fill: "#EEF",
        'stroke-width': 0    
    });
    
    var arm = paper.path("M" + x + "," + (y + 5) + "v-" + (l - 5)).attr({
        'stroke-width': 5,
        stroke: "#999"
    }).data("id", "arm");
        
    var weight = paper.path("M" + x + "," + (y-100) + "h12l-3,18h-18l-3-18h12").attr({
        'stroke-width': 0,
        fill: '#666'
    }).data("id", "weight");

    var vertex = paper.circle(x, y, 7).attr({
        'stroke-width': 0,
        fill: '#CCC'
    }).data("id", "vertex");

    var label = paper.text(x, y + 20, "").attr({
        "text-anchor": "center",
        "font-size": 14
    });

    var mn = paper.set(arm, weight);
    
    Raphael.easing_formulas.sinoid = function(n) { return Math.sin(Math.PI * n / 2) };

    function tick(obj, repeats) {      
        //Raphael summons the callback on each of the three objects in the set, so we
        //have to only call the sound once per iteration by associating it with one of the objects.
        //doesn't matter which one
        if (obj.data("id") === "arm") {
            tick_count += 1;
            // TIMESTAMP WHEN TICK OCCURS
            tickTime = performance.now();
            //messages.innerHTML += "metronomeTime:" + tickTime + "<br/>";
            barNum = document.getElementById("barNum");
            metroTick = tick_count % 4;
            // SHOW BAR NUMBER
            if (tick_count <= 4)
            {
                // Set to global var representing tick
                metroTick = tick_count;
                barNum.innerHTML = tick_count;
            }
            else if (metroTick == 0)  // 4th beat
            {
                metroTick = 4;
                barNum.innerHTML = 4;
            }
            else
            {
                barNum.innerHTML = metroTick;
            }

            // Increase metroMeasure
            if (metroTick == 1)
            {
                metroMeasure += 1;
            }

            // CHANGE BAR NUMBER COLOR
            if (barNum.innerText == "1")
            {
                barNum.style.color = "DarkRed";
            }
            else
            {
                barNum.style.color = "DarkBlue";
            }

            if (playSound) {    
                document.getElementById("tick").play();
            }
            tick_func(tick_count);            
            if (tick_count >= repeats) {
                mn.attr("transform", "R0 " + x + "," + y);    
                end_func();
            }    
        }
    }    

    return {
        start: function(tempo, repeats, tickf, donef) {
            if (tickf) {
                tick_func = tickf;
            }
            if (donef) {
                end_func = donef;
            }
            
            tick_count = 0;
            mn.attr("transform", "R-" + r + " " + x + "," + y);                
            
            //2 iterations per animation * 60000 ms per minute / tempo
            var interval = 120000 / tempo;

            var animationDone = function() { 
                tick(this, repeats); 
            };
            
            var ticktockAnimationParam = {
                "50%": { transform:"R" + r + " " + x + "," + y, easing: "sinoid", callback: animationDone },
                "100%": { transform:"R-" + r + " " + x + "," + y, easing: "sinoid", callback: animationDone }
            };
            
            metronomePlaying = true;
            //animation            
            var ticktock = Raphael.animation(ticktockAnimationParam, interval).repeat(repeats / 2);
            arm.animate(ticktock);
            weight.animateWith(arm, ticktockAnimationParam, ticktock); 
        },
        stop: function() {
            // Reset the bar number
            document.getElementById("barNum").innerHTML = "<br/>"
            metronomePlaying = false;
            mn.stop();
            mn.attr("transform", "R0 " + x + "," + y);                
            end_func();
        },
        shapes: function() {
            return {
                outline: outline,
                arm: arm,
                weight: weight,
                vertex: vertex          
            }
        },
        make_input: function(el) {
            $("<div />", {
                html:   "<span>tempo: </span>" + 
                        "<input class='metr_input' type='text' id='tempo' value='120' />" +
                        // "<span>ticks: </span>" +
                        // "<input class='metr_input' type='text' id='ticks' value='12000' />" +
                        "<button id='startstop'>start</button>"
            }).appendTo(el);
            
            $('#startstop').click(function() {
                // start animation
                if ($(this).html() === "start") {
                    $(this).html("stop");            
                    
                    //get values for tempo and ticks and restrict
                    var tempo = parseInt($('#tempo').val(), 10);
                    if (!tempo) { tempo = 120; }
                    else if (tempo > 200) { tempo = 200; }
                    else if (tempo < 30) { tempo = 30; }
                    $("#tempo").val(tempo);
                    globalTempo = tempo;

                    // Set the timedistinction value.
                    timeDistinction = ((60 / tempo) * 1000) * distinctFactor;
                    
                    // var ticks = parseInt($('#ticks').val(), 10);
                    // if (!ticks || ticks < 8) { ticks = 12000; }
                    // $("#ticks").val(ticks); 
                    
                    ticks = 12000;

                    m.start(tempo, ticks);
                    metronomePlaying = true;
                } else {
                    $(this).html("start");
                    metroMeasure = -1;
                    m.stop();
                    metronomePlaying = false;
                }
            });                         
        }
    };
};
