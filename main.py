from pytalk.record import AudioRecorder
from pytalk.googlestt import GoogleSTT

import commands, time, sys

recorder   = AudioRecorder(debug=True)
google_stt = GoogleSTT(None, debug=True) 

def say(x):
    commands.getoutput("say {0}".format(x))

def curtime():
    return commands.getoutput('date +"%I %M %p"')


while True:
    flac_file = recorder.record_and_process("/users/cam/github/pytalk/outfiles", min_time=1)
    if flac_file:
        gstt      = GoogleSTT(flac_file)
        trans     = gstt.get_translations(transform=lambda i: i.lower())
        print "You said: {0}".format(trans)

        if trans == "what is my name":
            say("Cameron")
        if trans == "what time is it":
            say(curtime())

        if trans == "hi there":
            say("no, goodbye")
        
 
