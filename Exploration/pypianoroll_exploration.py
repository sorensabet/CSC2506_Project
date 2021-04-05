import numpy as np
import pandas as pd 
import pypianoroll as pyp

datadir = '/Users/sorensabet/Desktop/MSC/CSC2506_Project/data/Generated MIDI/'
mt = pyp.read(datadir + 'major_36_16th_MEL_TWINKLE.mid')
print(mt)

# mt.resolution: Temporal resolution in timesteps per quarter note 
# mt.tempo:      Tempo of the song at each timestep. Don't need to worry about this because it is standardized. 

#mt.plot()

num_beats_trim = 4
mt2 = mt.copy()
mt2.set_resolution(12)
mt2.trim(0, num_beats_trim*mt2.resolution) # Trim  
mt2.binarize(1)
mt2 = mt2.pad_to_multiple(4)
mt2.plot()

track = mt2.tracks[0].pianoroll

# Okay. The NPY array seems to be: 
    # Timesteps based on beat resolution * 128 
    # Transposed version of pianoroll. 
    # I can manually assemble the MIDI data into that
    # Hopefully there is a function that extracts it from MIDI messages
    # So that I don't need to write one myself. 
    
    
# pypianoroll.Track.standardize(): 
    # returns standardized pypianoroll track (Standard Track)
    # Clips Pianoroll to [0, 127 and casts to np.uint8]

# Pypianoroll can parse pretty MIDI 
# Slow way: Import all generated MIDI files with pretty midi and generate npy files 
# Fast way: Find a way to convert in memory and generate npy files progrmatically 

# Read PyPianoRoll Source Code to find best way to split 
# Read CycleGAN paper to see what the npy files should contain. 
