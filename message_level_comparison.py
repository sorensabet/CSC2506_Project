import os 
import numpy as np
import pandas as pd

from mido import Message
from mido import MidiFile
from mido import MidiTrack
from mido import bpm2tempo
from mido import tempo2bpm 
from mido import MetaMessage

orig_path = r'C:\Users\Darth\Desktop\CSC2506_Project\MIDI_reconstruction_experiment\0\alb_esp1.mid'
new_path = r'C:\Users\Darth\Desktop\CSC2506_Project\MIDI_reconstruction_experiment\0\FILTERED_alb_esp1.mid'

mid1 = MidiFile(orig_path)
track1 = mid1.tracks[0]

mid2 = MidiFile(new_path)
track2 = mid2.tracks[0]

for i in range(0, len(track1)):
    str1 = str(track1[i])
    str2 = str(track2[i])
    
    
    if (str1 != str2):
        print('i: %d' % i)
        print(str1 == str2)
        print('Track1: %s' % str1)
        print('Track2: %s\n\n\n\n' % str2)
        input('Batman')