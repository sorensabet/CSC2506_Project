# Read in all messages and copy out to see if I get the same output using MIDO
import os 
import numpy as np
import pandas as pd

from mido import Message
from mido import MidiFile
from mido import MidiTrack
from mido import bpm2tempo
from mido import tempo2bpm 
from mido import MetaMessage

orig_path = r'C:\Users\Darth\Desktop\CSC2506_Project\MIDI_reconstruction_experiment\0\7ca554a7bb1fc0d97c433787d9e3d475.mid'
dupl_path = r'C:\Users\Darth\Desktop\CSC2506_Project\MIDI_reconstruction_experiment\0\DUPLICATED.mid'

# Step 1. Load in file with mido 
# Step 2. Loop through all tracks and messages
# Step 3. Copy them all to new mido object 
# Step 4. Save the new mido object 
# Step 5. Check if it copied correctly

mid = MidiFile(orig_path, clip=True)
new_mid = MidiFile(ticks_per_beat=mid.ticks_per_beat, type=mid.type)

msg_types = {}

for track in mid.tracks:
    new_track = MidiTrack(name=track.name)
    
    for msg in track:
        new_track.append(msg)
        
        if (msg.type in msg_types):
            msg_types[msg.type] += 1
        else:
            msg_types[msg.type] = 1
        
    new_mid.tracks.append(new_track)
    
new_mid.save(dupl_path)
print(msg_types)

### Hmmm. Something is not being copied across properly. I have to narrow down what it is.
# Does the MIDI file have any properties? 