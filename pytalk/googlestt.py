#!/usr/bin/python
import sys
import urllib2
import json
import pprint
import difflib

class GoogleSTT(object):
    def __init__(self, audiofile=None, debug=None):
        self.debug = debug
        if audiofile:
            self.data = open(audiofile).read()
        else:
            self.data = None
        self.url  = "https://www.google.com/speech-api/v1/recognize?xjerr=1&client=chromium&lang=en-US"
        self.headers = {"Content-Type":"audio/x-flac; rate=16000"}
    

    def set_file(self, audiofile):
        self.data = open(audiofile).read()

    def get_translations(self, transform=None):
        request = urllib2.Request(self.url, data=self.data, headers=self.headers)
        try:
            d_ret = urllib2.urlopen(request)
            d_ret = d_ret.read()

            result = self.process_results(d_ret)
            if transform and callable(transform):
                return transform(result)
            else:
                return result
        except OSError:
            # this was to get an actual printout of the error instead of just catching it.
            # this should NEVER error out
            sys.exit("This error should not have triggered")
    
    def process_results(self, r):
        r = json.loads(r)

        if self.debug:
            print "\n\n=====DEBUG=====\n\n"
            pprint.pprint(r)
            print "\n\n=====DEBUG=====\n\n"
            #print "You said '{0}' with a {1} assurance.".format()

        guess = r['hypotheses'][0]
        return guess['utterance'] # predicted speech

