import os
import time
import shutil
import pypianoroll
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pretty_midi

from tqdm import tqdm
from pypianoroll import Multitrack, Track, BinaryTrack
from mido import Message, MidiFile, MidiTrack, bpm2tempo, tempo2bpm, MetaMessage

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

def add_note(note, start_beat, length_in_beats):
    """
        note:               MIDI note number, from 0-127
        start_beat:         The beat on which the note starts playing, from start of the song
        length_in_beats:    The length of the note in beats 
    """
    
    note_on = {'type': 'note_on', 'note': i, 'start_beat': start_beat}
    note_off = {'type': 'note_off', 'note': i, 'start_beat': start_beat + length_in_beats}
    msgs = [note_on, note_off]
    return msgs

def add_chord(notes, start_beat, length_in_beats, note_type=None): 
    """
        notes:              A list of the notes to be included in the chord 
        start_beat:         See add_note
        length_in_beats:    See add_note
    """

    msgs = []
    for note in notes: 
        note_on = {'type': 'note_on', 'note': note, 'start_beat': start_beat}
        note_off = {'type': 'note_off', 'note': note, 'start_beat': start_beat + length_in_beats}
        msgs.append(note_on)
        msgs.append(note_off)
    return msgs

def makefile(all_notes, savedir=None, filename=None):
    
    df = pd.DataFrame.from_records(all_notes)                                  # Assemble dataframe from list of dictionaries
    df.sort_values(by=['start_beat'], inplace=True)
    df['ctime'] = df['start_beat']*480                                         # Use 480 ticks per beat 
    df['time'] = df['ctime'] - df['ctime'].shift(1)                            # MIDI commands are sequential, we need to go from cumulative time to time between events
    df = df[['type', 'note', 'time', 'start_beat', 'ctime']].fillna(0)
    df = df.astype({'type': 'category', 'time': int, 
                    'start_beat': float, 'ctime': float})
    df['velocity'] = np.where(df['type'] == 'note_on', 64, 0)
        
    # Create the track specific MIDI file 
    mid = MidiFile(ticks_per_beat=480, type=0)
    midiTrack = MidiTrack()
    
    # Tempo MIDI Message (Set to 120 BPM)
    midiTrack.append(MetaMessage('set_tempo', time=0, tempo=500000))

    # Time Signature MIDI Message (Standardize to 120bpm)
    midiTrack.append(MetaMessage('time_signature', time=0, numerator=4, denominator=4, 
                                 clocks_per_click=24, notated_32nd_notes_per_beat=8))

    # Key Signature MIDI Message (Shouldn't matter since MIDI note number determines the correct note)
    midiTrack.append(MetaMessage('key_signature', time=0, key='C'))
    
    # Individual Messages corresponding to notes 
    midiTrack += [Message(x[1],  note=int(x[2]), time=int(x[3]), velocity=int(x[6]), channel=0) for x in df.itertuples()]
    
    # End of Track MIDI Message
    midiTrack.append(MetaMessage('end_of_track', time=0))
    
    # Append Track to MIDI File
    mid.tracks.append(midiTrack)

    mid.save(savedir + '/' + filename)
    return None 


all_notes = []
savedir = '/Users/sorensabet/Desktop/MSC/CSC2506_Project/data/Generated MIDI'

# Adding notes 
# for c, i in enumerate(range(60, 64)):
#     all_notes += add_note(note=i, start_beat=c, length_in_beats=1)

# Adding chords
for c, i in enumerate(range(60,68,2)):
    all_notes += add_chord([i, i+4, i+7], c, 1)

makefile(all_notes, savedir, 'test.mid')
