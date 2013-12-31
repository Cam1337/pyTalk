
import wave
import pyaudio
import audiotools
import array, sys, struct, os, time, signal

from numpy import sqrt as n_sqrt
from numpy import mean as n_mean

class AudioRecorder(object):
    def __init__(self, chunk=1024, rate=16000, debug=False):
        self.debug    = debug
        self.chunk    = chunk
        self.rate     = rate
        self.channels = 2
        self.format   = pyaudio.paInt16

        self.silence_threshold = 500 # experiment with this variable..

    def is_silence(self, a_data):
        # RMS calculation: http://en.wikipedia.org/wiki/Root_mean_square
        # return n_sqrt(n_mean(a_data**2, axis=axis)) < self.silence_threshold # numpy.sqrt and numpy.mean
        return max(a_data) < self.silence_threshold # I think the solution above is better

    def normalize_volume(self, recording):

        recording = map(abs, recording)
        
        norm = 32768 / max(recording) # 2**15
        norm_rec = array.array('h') # signed short int
        for itm in recording:
            norm_rec.append(int(itm) * norm)
        return norm_rec
    
    def trim(self, data):
        print "**trimming silence**"
        # trim silence from front and back (abstract wrapper)
        def f_trim(data):
            # trim silence from the front of the file
            new_data = array.array('h')
            started_talking = 0
            
            for bit in data:
                if started_talking == 0:
                    if bit < self.silence_threshold: 
                        continue
                    started_talking = 1
                    new_data.append(bit)
                else:
                    new_data.append(bit)
            
            return new_data
    
        data = f_trim(data) # trim front of file
        data.reverse()      # make back of file front of file
        data = f_trim(data) # trim front (back) of file
        data.reverse()      # re-orient the file 

        return data
            
    
    def record(self):
        audio  = pyaudio.PyAudio()
        stream = audio.open(format=self.format, channels=self.channels, rate=self.rate, frames_per_buffer=self.chunk, input=True, output=True)
        
        time_silent  = 0
        talk_started = 0
        
        time_talk_start = 0
        time_talk_end   = 0
        
        recording = array.array('h') # array of signed shorts http://docs.python.org/2/library/array.html#module-array

        try: 
            while True:
                data = stream.read(self.chunk)
                data = array.array('h', data)
                if self.debug:
                    print """Data: {0} items. Talk Started: {1}. Time Silent: {2}""".format(len(data), talk_started, time_silent)

                # if the machine processes endianess differently than the default for pyaudio  
                if sys.byteorder == 'big': # http://docs.python.org/2/library/sys.html#sys.byteorder
                    data.byteswap() # http://en.wikipedia.org/wiki/Endianness#Endianness_in_files_and_byte_swap
                                    # http://docs.python.org/2/library/array.html#array.array.byteswap

                recording.extend(data)
                                
                if self.is_silence(data):
                    if talk_started:
                        time_silent += 1
                    if time_silent >= 5: 
                        time_talk_end = time.time()
                        break
                else:
                    time_silent = 0
                    if not talk_started:
                        time_talk_start = time.time()
                        talk_started = 1
        except KeyboardInterrupt, e:
           return None 
                
        
        # finished with recording

        allow_interrupt = signal.signal(signal.SIGINT, signal.SIG_IGN) # ignore keyboard interrupts
        
        width = audio.get_sample_size(self.format)

        # close all stream related functions/processes
        stream.stop_stream()
        stream.close()
        
        # terminate the pyaudio instance
        audio.terminate()

        total_time = time_talk_end - time_talk_start 

        signal.signal(signal.SIGINT, allow_interrupt) # restore keyboard interrupts
        
        return (recording, width, total_time)

    def write_to_file(self, path, recording, width):
        _time = time.time()
        w_path = "{0}/out_{1}.wav".format(path, _time)
        if self.debug:
            print "**writing wav file to **"
        data = struct.pack('<' + ('h'*len(recording)), *recording)

        wf = wave.open(w_path, 'wb')
        wf.setnchannels(2)
        wf.setsampwidth(width)
        wf.setframerate(self.rate)
        wf.writeframes(data)
        wf.close()

        return _time 
    
    def convert_to_flac(self, path, r_hash):
        w_path = "{0}/out_{1}.wav".format(path, r_hash)
        n_path = "{0}/out_{1}.flac".format(path, r_hash)
        if self.debug:
            print "**converting {0}/out_{1}.wav to {0}/out_{1}.flac**".format(path, r_hash)
        audiotools.open(w_path).convert(n_path, audiotools.FlacAudio)
        return n_path
    
    def record_and_process(self, path, min_time=1):
        r_value = self.record()
        if r_value == None:
            raw_input("Press [ENTER] to start listening again...")
            return None
        recording, width, total = r_value 
        if self.debug:
            print "Talk time is {0}".format(total)
        if total < min_time:
            return None
        
        recording = self.trim(recording)
        #recording = self.normalize_volume(recording)

        r_hash = self.write_to_file(path, recording, width)
        n_path = self.convert_to_flac(path, r_hash)

        return n_path
        
        



