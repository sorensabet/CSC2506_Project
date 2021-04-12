import os 
import sys
import math
import shutil
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from mido import Message, MidiFile, MidiTrack, bpm2tempo, tempo2bpm, MetaMessage
#from write_midi import write_piano_roll_to_midi

import pretty_midi
import pypianoroll
import matplotlib.pyplot as plt

pd.options.mode.chained_assignment = None

np.random.seed(0)

def set_piano_roll_to_instrument(piano_roll, instrument, velocity=64, tempo=120.0, beat_resolution=4):
    # Calculate time per pixel
    tpp = 60.0 / tempo / float(beat_resolution)      # 0.125 seconds per pixel 
    threshold = 60.0 / tempo / 4                     # 0.125 (unit unclear)
    phrase_end_time = (60.0 / tempo) * piano_roll.shape[1] / beat_resolution
    
    # Create piano_roll_search that captures note onsets and offsets
    orig_piano_roll = piano_roll
    piano_roll = piano_roll.reshape((piano_roll.shape[0] * piano_roll.shape[1], piano_roll.shape[2]))   
    piano_roll_diff = np.concatenate((np.zeros((1, 128), dtype=int), piano_roll, np.zeros((1, 128), dtype=int)))
    piano_roll_search = np.diff(piano_roll_diff.astype(int), axis=0)
    # Iterate through all possible(128) pitches

    for note_num in range(128):
        #print('Note Num: %d' % note_num)
        # Search for notes
        start_idx = (piano_roll_search[:, note_num] > 0).nonzero()
        start_time = list(tpp * (start_idx[0].astype(float)))
        # print('start_time:', start_time)
        # print(len(start_time))
        end_idx = (piano_roll_search[:, note_num] < 0).nonzero()
        end_time = list(tpp * (end_idx[0].astype(float)))
        # print('end_time:', end_time)
        # print(len(end_time))
        duration = [pair[1] - pair[0] for pair in zip(start_time, end_time)]
        # print('duration each note:', duration)
        # print(len(duration))

        temp_start_time = [i for i in start_time]
        temp_end_time = [i for i in end_time]

        for i in range(len(start_time)):
            #print(start_time)
            if start_time[i] in temp_start_time and i != len(start_time) - 1:
                # print('i and start_time:', i, start_time[i])
                t = []
                current_idx = temp_start_time.index(start_time[i])
                for j in range(current_idx + 1, len(temp_start_time)):
                    # print(j, temp_start_time[j])
                    if temp_start_time[j] < start_time[i] + threshold and temp_end_time[j] <= start_time[i] + threshold:
                        # print('popped start time:', temp_start_time[j])
                        t.append(j)
                        # print('popped temp_start_time:', t)
                for _ in t:
                    temp_start_time.pop(t[0])
                    temp_end_time.pop(t[0])
                # print('popped temp_start_time:', temp_start_time)

        start_time = temp_start_time
        # print('After checking, start_time:', start_time)
        # print(len(start_time))
        end_time = temp_end_time
        # print('After checking, end_time:', end_time)
        # print(len(end_time))
        duration = [pair[1] - pair[0] for pair in zip(start_time, end_time)]
        # print('After checking, duration each note:', duration)
        # print(len(duration))

        if len(end_time) < len(start_time):
            d = len(start_time) - len(end_time)
            start_time = start_time[:-d]
        # Iterate through all the searched notes
        for idx in range(len(start_time)):
            if duration[idx] >= threshold:
                # Create an Note object with corresponding note number, start time and end time
                note = pretty_midi.Note(velocity=velocity, pitch=note_num, start=start_time[idx], end=end_time[idx])
                # Add the note to the Instrument object
                instrument.notes.append(note)
            else:
                if start_time[idx] + threshold <= phrase_end_time:
                    # Create an Note object with corresponding note number, start time and end time
                    note = pretty_midi.Note(velocity=velocity, pitch=note_num, start=start_time[idx],
                                            end=start_time[idx] + threshold)
                else:
                    # Create an Note object with corresponding note number, start time and end time
                    note = pretty_midi.Note(velocity=velocity, pitch=note_num, start=start_time[idx],
                                            end=phrase_end_time)
                # Add the note to the Instrument object
                instrument.notes.append(note)
    # Sort the notes by their start time
    instrument.notes.sort(key=lambda note: note.start)
    # print(max([i.end for i in instrument.notes]))
    # print('tpp, threshold, phrases_end_time:', tpp, threshold, phrase_end_time)


def write_piano_roll_to_midi(piano_roll, program_num=0, is_drum=False, velocity=64,
                             tempo=120.0, beat_resolution=16):
    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    # Create an Instrument object
    instrument = pretty_midi.Instrument(program=program_num, is_drum=is_drum)
    # Set the piano roll to the Instrument object

    set_piano_roll_to_instrument(piano_roll, instrument, velocity, tempo, beat_resolution)
    
    mido = generate_mido(instrument.notes)
    
    # Add the instrument to the PrettyMIDI object
    #midi.instruments.append(instrument)
    # Return MIDI file for writing out in other file 
    return mido, instrument.notes

def generate_mido(notes): 
    
    note_dict = []
    for n in notes: 
        note_dict.append({'note': n.pitch, 'start(s)': n.start, 'end(s)': n.end, 'velocity': 64})
    df = pd.DataFrame.from_records(note_dict)
    
    dfs = df[['note', 'start(s)']]
    dfs['type'] = 'note_on'
    dfs['start_beat'] = dfs['start(s)']*2
    
    dfe = df[['note', 'end(s)']]
    dfe['type'] = 'note_off'
    dfe['start_beat'] = dfe['end(s)']*2
    
    df2 = pd.concat([dfs[['note', 'type', 'start_beat']], dfe[['note', 'type', 'start_beat']]])
    df2.sort_values(by=['start_beat'], inplace=True)
    df2['ctime'] = df2['start_beat']*480                                         # Use 480 ticks per beat 
    df2['time'] = df2['ctime'] - df2['ctime'].shift(1)                            # MIDI commands are sequential, we need to go from cumulative time to time between events
    df2 = df2.fillna(0)
    
    ### USING MIDO TO GENERATE MIDI FILES #### 
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
       
    midiTrack += [Message(x[2],  note=int(x[1]), time=int(x[5]), velocity=64, channel=0) for x in df2.itertuples()]
    
    # End of Track MIDI Message
    midiTrack.append(MetaMessage('end_of_track', time=0))
    
    # Append Track to MIDI File
    mid.tracks.append(midiTrack)
    
    #mid.save(savedir + '/' + filename + '_' + str(s) + '.mid')
    # print('Generated MIDO file!')
    # print(savedir + '/' + filename + '_' + str(s) + '.mid')
    return mid 

def add_note(note, start_beat, length_in_beats):
    """
        note:               MIDI note number, from 0-127
        start_beat:         The beat on which the note starts playing, from start of the song
        length_in_beats:    The length of the note in beats 
    """
    
    note_on = {'type': 'note_on', 'note': note, 'start_beat': start_beat}
    note_off = {'type': 'note_off', 'note': note, 'start_beat': start_beat + length_in_beats}
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
    df['bar'] = (df['start_beat']/4).astype(int)
    df['segment'] = (df['bar']/4).astype(int)
    df['bar'] += 1 # Switch from 0 index to 1 index
    df_orig = df.copy()    
    num_bars = df['bar'].max()
    multiple_4_bars = num_bars % 4
    unq_start_beats = sorted(df['start_beat'].unique())
    beat_length = unq_start_beats[1] - unq_start_beats[0]
    
    # Make sure all segments are exactly 4 bars 
    # If shorter, duplicate until we have at least 4 bars 
    # If longer, duplicate so we have enough 4 bar segments, then cut 
    
    if (multiple_4_bars != 0 and num_bars <4): 
        #print('Extending Track')
        
        # Find how many beats of content there currently are 
        # Find out how many beats I need to add 
        # Loop over the dataframe and duplicate it until I get enough beats 
        max_beat = unq_start_beats[-1]
        num_iters = math.ceil((16 - beat_length)/max_beat) # Figure out how many times we need to copy this 
        
        new_dfs = [df]
        for i in range(1, num_iters): 
            tdf = df.copy()
            tdf['start_beat'] += i*max_beat + beat_length
            new_dfs.append(tdf)
        df = pd.concat(new_dfs)
        df['bar'] = (df['start_beat']/4).astype(int)
        df['segment'] = (df['bar']/4).astype(int)
        df['bar'] += 1 # Switch from 0 index to 1 index
        df = df.loc[df['segment'] == 0]
    elif (multiple_4_bars != 0 and num_bars >4):       
        #print('Splitting Track')
        dupl = df.copy()
        dupl['start_beat'] += df['start_beat'].max() + beat_length # Start duplicated notes on the next beat
        df = pd.concat([df, dupl])
        df['bar'] = (df['start_beat']/4).astype(int)
        df['segment'] = (df['bar']/4).astype(int)
        df['bar'] += 1 # Switch from 0 index to 1 index
        df = df.loc[df['segment'] <= int(num_bars/4)]  
        
        # Need to make sure that note_offs also end at the end of the 4 bars
        
    else: 
        #print('Did not duplicate or split track!')
        pass

    # Removing last n occurences of note_on commands where 
    # n is the difference between # of note_on commands and note_off commands in dataframe
    # (Prevents extra note_on's with no note_off command as a result of extending/shortening to 4-bar segments)
    
    # dft = df.loc[(df['type'] == 'note_off')]
    # dft = dft.loc[dft['start_beat'] <= (dft['segment'])*16 + beat_length]
    # dft = dft.loc[dft['segment'] > 0]
    
    df['start_beat'] = np.where((df['type'] == 'note_off') & 
                            (df['start_beat'] <= (df['segment']*16 + beat_length)) & 
                            (df['segment'] > 0), 
                            (df['segment'])*16 - 0.001,  # Replace with (segment + 1)*16
                            df['start_beat']) 
    df['bar'] = (df['start_beat']/4).astype(int)
    df['segment'] = (df['bar']/4).astype(int)
    
    df.sort_values(by=['start_beat'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['MIDI_order'] = df.index
        
    df['note_type_val'] = np.where(df['type'] == 'note_on', 1, -1)
    df['note_type_sum'] = df['note_type_val'].cumsum()
    num_noteon_to_remove = df['note_type_sum'].iloc[-1]
    
    note_on_idxs = list(df.loc[df['type'] == 'note_on'].index)
    note_on_idxs = note_on_idxs[:len(note_on_idxs) - num_noteon_to_remove]
    note_off_idxs = list(df.loc[df['type'] == 'note_off'].index)
    all_idxs = note_on_idxs + note_off_idxs
    df = df.iloc[all_idxs]
    df.sort_values(by=['MIDI_order'], inplace=True)

    df['ctime'] = df['start_beat']*480                                         # Use 480 ticks per beat 
    df['time'] = df['ctime'] - df['ctime'].shift(1)                            # MIDI commands are sequential, we need to go from cumulative time to time between events
    df = df[['type', 'note', 'time', 'start_beat', 'ctime', 'segment']].fillna(0)   # Split > 16 bars into longer segments. 
    df = df.astype({'type': 'category', 'time': int, 
                    'start_beat': float, 'ctime': float})
    df['velocity'] = np.where(df['type'] == 'note_on', 64, 0)
    
    for s in df['segment'].unique(): 
        #print(s)
        
        sdf = df.loc[df['segment'] == s][['type', 'note', 'time', 'velocity', 'start_beat']]

        
        #### USING PRETTY_MIDI + PYPIANOROLL TO GENERATE MIDI + NPY FILES
        sdf['seconds'] = sdf['start_beat']*0.5 # 1 second = 2 beats @ 120 bpm
        sdf_start = sdf.loc[sdf['type'] == 'note_on'].rename(columns={'seconds': 'start_time(s)'})[['note', 'velocity', 'start_time(s)']].reset_index(drop=True)
        sdf_end = sdf.loc[sdf['type'] == 'note_off'].rename(columns={'seconds': 'end_time(s)'})[['end_time(s)']].reset_index(drop=True)
        
        sdf_prettymidi = sdf_start.merge(sdf_end, left_index=True, right_index=True, how='left')
        sdf_prettymidi['start_time(s)'] -= sdf_prettymidi['start_time(s)'].min()
        sdf_prettymidi['end_time(s)'] = sdf_prettymidi['start_time(s)'] + beat_length*0.5
        sdf_prettymidi['end_time(s)'] = np.where(sdf_prettymidi['end_time(s)'] > 8.0, 8.0, sdf_prettymidi['end_time(s)'])
        
        sdf_pianoroll = sdf_prettymidi[['note', 'start_time(s)', 'end_time(s)']]
        sdf_pianoroll['start_timestep'] = (sdf_pianoroll['start_time(s)']*32).astype(int)
        sdf_pianoroll['end_timestep'] = (sdf_pianoroll['end_time(s)']*32).astype(int)
        
        
        # print(s)
        # print(filename)
        # Making a file using pretty_midi instead of MIDO for easier npy file generation 
        pretty_mid = pretty_midi.PrettyMIDI()
        piano = pretty_midi.Instrument(program = 1)
        
        ### NEW PLAN: Assemble the npy array manually  
        # 256 timesteps (beat_resolution=16*16 beats) * 128 pitches 
        pianoroll = np.zeros((256, 128))
        
        for tup in sdf_pianoroll.itertuples(): 
            pianoroll[tup[4]:tup[5], tup[1]] = 1 # Turn the note on for these timesteps 
                
        for x in sdf_prettymidi.itertuples(): 
            note = pretty_midi.Note(velocity=64, 
                                    pitch=int(x[1]), 
                                    start=float(x[3]), 
                                    end=float(x[4]))
            piano.notes.append(note)
        pretty_mid.instruments.append(piano)
        
        # Reconstructing MIDI from pianoroll to compare against original
        mido_mid_recr, pianoroll_notes = write_piano_roll_to_midi(pianoroll.reshape((1,256,128)), beat_resolution=16)
        
                
        mid_file = filename + '_' + str(s) + '.mid'
        npy_file = filename + '_' + str(s) + '.npy'
        mid_file2 = filename + '_' + str(s) + '_npy-MIDI.mid'

        # Generate MIDI files as reconstructed by piano rolls 
        if (np.random.uniform(0,1) <= 0.8):
            if (('major' in filename) or ('dominant' in filename)):
                #pretty_mid.write(str(savedir / 'major/train_midi' / mid_file))
                np.save(savedir / 'major/train' / npy_file, pianoroll)
                mido_mid_recr.save(str(savedir / 'major/train_midi'/ mid_file2))

            else:    
                #pretty_mid.write(str(savedir / 'minor/train_midi' / mid_file))
                np.save(savedir / 'minor/train' / npy_file, pianoroll)
                mido_mid_recr.save(str(savedir / 'minor/train_midi'/ mid_file2))

        else:
            if (('major' in filename) or ('dominant' in filename)):
                #pretty_mid.write(str(savedir / 'major/test_midi' / mid_file))
                np.save(savedir / 'major/test' / npy_file, pianoroll)
                mido_mid_recr.save(str(savedir / 'major/test_midi'/ mid_file2))
            else:
                #pretty_mid.write(str(savedir / 'minor/test_midi' / mid_file))
                np.save(savedir / 'minor/test' / npy_file, pianoroll)
                mido_mid_recr.save(str(savedir / 'minor/test_midi'/ mid_file2))
    return None

def gen_chord_prog_1(run, savedir, key, nlk, nl): 
    if (run == False):
        return None 
               
    major_semitones = [4, 3, 5, -5, -3, -7, # Chord 1 
                       4, 3, 5, -5, -3, -7, # Chord 2
                       4, 3, 5, -5, -3, -2, # Chord 3
                       4, 3, 5, -5, -3, -2] # Chord 4 
    minor_semitones = [3, 4, 5, -5, -4, -6, # Chord 1
                        3, 4, 5, -5, -4, -7, # Chord 2
                        3, 4, 5, -5, -4, -1, # Chord 3 
                        3, 4, 5, -5, -4, -3] # Chord 4 
    scales = {'major': major_semitones, 'minor': minor_semitones}            

    for scale in scales.keys(): 
        all_notes = [] 
        note = key 
        for c, i in enumerate(scales[scale]): # Step through transitions 
            all_notes += add_note(note=note, start_beat=nl*c, length_in_beats=nl) # Right hand
            all_notes += add_note(note=(note-12), start_beat=nl*c, length_in_beats=nl) # Right hand
            note += i
        makefile(all_notes, savedir, '{}_{}_{}_CHORD_PROG_1'.format(scale, key, nlk))
    return None 

def gen_chord_prog_2(run, savedir, key, nlk, nl): 
       # MAJ     MIN 
       # CEGC    CEbGC
       # GCEG    GCEbG
       # CEGC    CEbGC
       # GCEG    GCEbG
       # CFAC    CFAbC
       # FACF    FAbCF 
       # CFAC    CFAbC
       # FACF    FAbCF
       # CEGC    CEbGC
       # GCEG    GCEbG
       # CEGC    CEbGC
       # GCEG    GCEbG
       # GBDG    GBbDG
       # ACFA    ACEA
       # BDGD    BbDGBb
       # CEGC    CEbGC
        
    if (run == False):
        return None 
        
    major_semitones = [[ 0, 4, 7, 12],[-5, 0, 4, 7],
                       [ 0, 4, 7, 12],[-5, 0, 4, 7],
                       [ 0, 5, 9, 12],[ -7, -3, 0, 5],
                       [ 0, 5, 9, 12],[ -7, -3, 0, 5],
                       [ 0, 4, 7, 12],[-5, 0, 4, 7],
                       [ 0, 4, 7, 12],[-5, 0, 4, 7],
                       [ -5, -1, 2, 7], [ -3, 0, 5, 9],
                       [ -1, 2, 7, 11], [0, 4, 7,12]]
    
    minor_semitones = [[ 0, 3, 7, 12],[-5, 0, 3, 7],
                       [ 0, 3, 7, 12],[-5, 0, 3, 7],
                       [ 0, 5, 8, 12],[ -7, -4, 0, 5],
                       [ 0, 5, 8, 12],[ -7, -4, 0, 5],
                       [ 0, 3, 7, 12],[-5, 0, 3, 7],
                       [ 0, 3, 7, 12],[-5, 0, 3, 7],
                       [ -5, -2, 2, 7], [-3, 0, 4, 9],
                       [ -2, 2, 7, 10], [0, 3, 7,12]]
    
    scales = {'major': major_semitones, 'minor': minor_semitones}   
         
    for scale in scales.keys(): 
        all_notes = [] 
        note = key 
        for c, i in enumerate(scales[scale]): # Step through transitions 
            all_notes += add_chord(notes=[note + ch_n for ch_n in i], #RH
                                   start_beat=nl*c, 
                                   length_in_beats=nl)
        makefile(all_notes, savedir, '{}_{}_{}_CHORD_PROG_2'.format(scale, key, nlk))
    return None 

def gen_mel_1(run, savedir, key, nlk, nl):
    if (run == False):
        return False 
    # Major Version           # Minor Version 
    # C G E G C G F C         # C G E G C G F C 
    # D G F G D G F D         # D G F G D G F D
    # E G F G E G F G         # Eb G F G Eb G F G
    # F A G A F E D C         # F Ab G A F Eb D C 
    
    if run==False: 
        return None 

    major_semitones = [7, -2, 2, 5, -5, -2, 2, 
                       -5, 5, -2, 2, 7, -7, -2, 2,
                       -3, 3, -2, 2, 9, -9, -2, 2,
                       -2, 4, -2, 2, 8, -1, -2, -2, -2] 
    minor_semitones = [7, -2, 2, 5, -5, -2, 2, 
                       -5, 5, -2, 2, 7, -7, -2, 2,
                       -4, 4, -2, 2, 8, -8, -2, 2,
                       -2, 3, -1, 1, 9, -2, -1, -2, -2] 
    scales = {'major': major_semitones, 'minor': minor_semitones}            
     
    for scale in scales.keys(): 
        all_notes = [] 
        note = key 
        for c, i in enumerate(scales[scale]): # Step through transitions 
            all_notes += add_note(note=note, start_beat=nl*c, length_in_beats=nl) # Right hand
            all_notes += add_note(note=(note-12), start_beat=nl*c, length_in_beats=nl) # Right hand
            note += i
        makefile(all_notes, savedir, '{}_{}_{}_MEL_1'.format(scale, key, nlk))
    return None 

def gen_mel_2(run, savedir, key, nlk, nl): 
    # Major Version        # Minor Version 
    # C D E F              # C D Eb F
    # D E F G              # D Eb F G
    # E F G A              # Eb F G Ab
    # F G A C              # F Ab B C

    if (run == False):
        return None 

    major_semitones = [2, 2, 1, 
                       -3, 2, 1, 2, 
                       -3, 1, 2, 2, 
                       -2, 2, 2, 1, 2] 
    minor_semitones = [2, 1, 2, 
                       -3, 1, 2, 2, 
                       -4, 2, 2, 1 ,
                       -3, 3, 3, 1, 1] 
    scales = {'major': major_semitones, 'minor': minor_semitones}            

    for scale in scales.keys(): 
        all_notes = [] 
        note = key 
        for c, i in enumerate(scales[scale]): # Step through transitions 
            all_notes += add_note(note=note, start_beat=nl*c, length_in_beats=nl) # Right hand
            all_notes += add_note(note=(note-12), start_beat=nl*c, length_in_beats=nl) # Right hand
            note += i
        makefile(all_notes, savedir, '{}_{}_{}_MEL_2'.format(scale, key, nlk))

def gen_mel_twinkle(run, savedir, key, nlk, nl): 
    if run == False:
        return None 

    # Slighlty modified Twinkle Twinkle Little Star
    # Written to work with single note length 
    
    # Major Version
    # C C G G A A G G F F E E D D C C 
    # G G F F E E D D G G F F E E D D 
    # C C G G A A G G F F E E D D C C 
    
    # Minor Version
    # C C G G Ab Ab G G F F Eb Eb D D C C 
    # G G F F Eb Eb D D G G F F Eb Eb D D 
    # C C G G Ab Ab G G F F Eb Eb D D C C 
    
    major_semitones = [0, 7, 0, 2, 0, -2, 0, -2, 0, -1, 0, -2, 0, -2, 0, 
                       7, 0, -2, 0, -1, 0, -2, 0, 5, 0, -2, 0, -1, 0, -2, 0,
                       -2, 0, 7, 0, 2, 0, -2, 0, -2, 0, -1, 0, -2, 0, -2, 0, 0,]
                    
    minor_semitones = [0, 7, 0, 1, 0, -1, 0, -2, 0, -2, 0, -1, 0, -2, 0, 
                       7, 0, -2, 0, -2, 0, -1, 0, 5, 0, -2, 0, -2, 0, -1, 0,
                       -2, 0, 7, 0, 1, 0, -1, 0, -2, 0, -2, 0, -1, 0, -2, 0, 0]
                    
    scales = {'major': major_semitones, 'minor': minor_semitones}            
     
    for scale in scales.keys(): 
        all_notes = [] 
        note = key 
        for c, i in enumerate(scales[scale]): # Step through transitions 
            all_notes += add_note(note=note, start_beat=nl*c, length_in_beats=nl) # Right hand
            all_notes += add_note(note=(note-12), start_beat=nl*c, length_in_beats=nl) # Right hand
            note += i
        makefile(all_notes, savedir, '{}_{}_{}_MEL_TWINKLE'.format(scale, key, nlk))
    return None 

def gen_mel_happybday(run, savedir, key, nlk, nl): 
    if run == False:
        return None 
    # Modified Happy Birthday (single note length)
    
    # Major Version
    # C C D C F E E C 
    # C C D C G F F C
    # C C A F F E E D 
    # Bb Bb A F G F F 
    
    # Minor Version
    # C C D C F Eb Eb C 
    # C C D C G F  F  C
    # C C Ab F F Eb Eb D 
    # Bb Bb Ab F G F F 

    major_semitones = [0, 2, -2, 5, -1, 0, -4, 
                       0, 0, 2, -2, 7, -2, 0, -5,
                       0, 0, 9, -4, 0, -1, 0, -2, 
                       8, 0, -1, -4, 2, -2, 0, 0]
                    
    minor_semitones = [0, 2, -2, 5, -2, 0, -3, 
                       0, 0, 2, -2, 7, -2, 0, -5,
                       0, 0, 8, -3, 0, -2, 0, -1, 
                       8, 0, -2, -3, 2, -2, 0, 0]
                        
    scales = {'major': major_semitones, 'minor': minor_semitones}            
 
    for scale in scales.keys(): 
        all_notes = [] 
        note = key 
        for c, i in enumerate(scales[scale]): # Step through transitions 
            all_notes += add_note(note=note, start_beat=nl*c, length_in_beats=nl) # Right hand
            all_notes += add_note(note=(note-12), start_beat=nl*c, length_in_beats=nl) # Right hand
            note += i
        makefile(all_notes, savedir, '{}_{}_{}_MEL_HAPPYBDAY'.format(scale, key, nlk))
    return None 

def gen_scales(run, savedir, key, nlk, nl, num_octaves_scale):
    if (run == False):
        return None 
    
    major_semitones = [2,2,1,2,2,2,1]
    minor_natural_semitones = [2,1,2,2,1,2,2]
    minor_harmonic_semitones = [2,1,2,2,1,3,1]
    minor_melodic_semitones = [2,1,2,2,2,2,1]

    scales = {"major_scale": major_semitones, "minor_natural_scale": minor_natural_semitones, "minor_harmonic_scale": minor_harmonic_semitones, "minor_melodic_scale": minor_melodic_semitones}
    for scale in scales:
        all_notes = []
        all_notes_lh_alternating = []
        note = key
        for c, i in enumerate(scales[scale]): # Iterate over all notes within the scale
            for octave in range(num_octaves_scale):
                all_notes += add_note(note=note + 12*octave, start_beat=(c+7*octave)*nl, length_in_beats=nl) # Right hand
                all_notes += add_note(note=note + 12*(octave-1), start_beat=(c+7*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(c+7*octave) + 1)*nl, length_in_beats=nl) # Right hand
                all_notes_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=(2*(c+7*octave))*nl, length_in_beats=nl) # Left hand
            note += i
        all_notes += add_note(note=key + 12*num_octaves_scale, start_beat=(7*num_octaves_scale)*nl, length_in_beats=nl) # Right hand
        all_notes += add_note(note=key + 12*(num_octaves_scale-1), start_beat=(7*num_octaves_scale)*nl, length_in_beats=nl) # Left hand
        all_notes_lh_alternating += add_note(note=key + 12*num_octaves_scale, start_beat=(2*(7*num_octaves_scale) + 1)*nl, length_in_beats=nl) # Right hand
        all_notes_lh_alternating += add_note(note=key + 12*(num_octaves_scale-1), start_beat=(2*(7*num_octaves_scale))*nl, length_in_beats=nl) # Left hand
        makefile(all_notes, savedir, '{}_{}_{}'.format(scale, key, nlk))
        makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating'.format(scale, key, nlk))
 
    return None 

def gen_dec_scales(run, savedir, key, nlk, nl, num_octaves_scale):
    if (run == False):
        return None
    
    major_semitones_dec = [-1,-2,-2,-2,-1,-2,-2]
    minor_natural_semitones_dec = [-2,-2,-1,-2,-2,-1,-2]
    minor_harmonic_semitones_dec = [-1,-3,-1,-2,-2,-1,-2]
    minor_melodic_semitones_dec = [-1,-2,-2,-2,-2,-1,-2]

    scales_dec = {"major_scale_dec": major_semitones_dec, "minor_natural_scale_dec": minor_natural_semitones_dec, 
                  "minor_harmonic_scale_dec": minor_harmonic_semitones_dec, "minor_melodic_scale_dec": minor_melodic_semitones_dec}
    
    # Write descending scales for all keys
    for scale in scales_dec:
        all_notes = []
        all_notes_lh_alternating = []
        note = key
        for c, i in enumerate(scales_dec[scale]): # Iterate over all notes within the scale
            for octave in range(num_octaves_scale):
                all_notes += add_note(note=note - 12*octave, start_beat=(c+7*octave)*nl, length_in_beats=nl) # Right hand
                all_notes += add_note(note=note - 12*(octave+1), start_beat=(c+7*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_lh_alternating += add_note(note=note - 12*octave, start_beat=(2*(c+7*octave) + 1)*nl, length_in_beats=nl) # Right hand
                all_notes_lh_alternating += add_note(note=note - 12*(octave-1), start_beat=(2*(c+7*octave))*nl, length_in_beats=nl) # Left hand
            note += i
        all_notes += add_note(note=key - 12*num_octaves_scale, start_beat=(7*num_octaves_scale)*nl, length_in_beats=nl) # Right hand
        all_notes += add_note(note=key - 12*(num_octaves_scale+1), start_beat=(7*num_octaves_scale)*nl, length_in_beats=nl) # Left hand
        all_notes_lh_alternating += add_note(note=key - 12*num_octaves_scale, start_beat=(2*(7*num_octaves_scale) + 1)*nl, length_in_beats=0.5) # Right hand
        all_notes_lh_alternating += add_note(note=key - 12*(num_octaves_scale-1), start_beat=(2*(7*num_octaves_scale))*nl, length_in_beats=0.5) # Left hand
        makefile(all_notes, savedir, '{}_{}_{}'.format(scale, key, nlk))
        makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating'.format(scale, key, nlk))  
    return None 
    
def gen_triads(run, savedir, key, nlk, nl, num_octaves_scale): 
    if run==False:
        return None
    
    major_chord_semitones = [4, 3, 5]
    minor_chord_semitones = [3, 4, 5]
    
    chords = {"major_chord": major_chord_semitones, "minor_chord": minor_chord_semitones}
    
    for chord in chords:
        all_notes = []
        all_notes_broken = []
        all_notes_alternating = []
        all_notes_arpeggios = []
        all_notes_lh_alternating = []
        all_notes_alternating_lh_alternating = []
        all_notes_arpeggios_lh_alternating = []
        note = key
        
        for c, i in enumerate(chords[chord]): # Iterate over all starting keys of the chords
            second_note = note + chords[chord][c%3]
            third_note = second_note + chords[chord][(c+1)%3]
            for octave in range(num_octaves_chord):
                # Solid
                all_notes += add_chord(notes=[note + 12*octave, second_note + 12*octave, third_note + 12*octave, note + 12*(1+octave)], 
                                       start_beat=(c+3*octave)*nl, length_in_beats=nl)
                all_notes += add_chord(notes=[note + 12*(octave-1), second_note + 12*(octave-1), third_note + 12*(octave-1), note + 12*octave], 
                                       start_beat=(c+3*octave)*nl, length_in_beats=nl)

                # Broken
                all_notes_broken += add_note(note=note + 12*octave, start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_broken += add_note(note=second_note + 12*octave, start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note + 12*octave, start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=note + 12*(1+octave), start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                all_notes_broken += add_note(note=note + 12*(octave-1), start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_broken += add_note(note=second_note + 12*(octave-1), start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note + 12*(octave-1), start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=note + 12*octave, start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                # Alternating
                all_notes_alternating += add_note(note=note + 12*octave, start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating += add_note(note=second_note + 12*octave, start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note + 12*octave, start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=note + 12*(1+octave), start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                all_notes_alternating += add_note(note=note + 12*(octave-1), start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_alternating += add_note(note=second_note + 12*(octave-1), start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note + 12*(octave-1), start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=note + 12*octave, start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                # Arpeggios
                all_notes_arpeggios += add_note(note=note + 12*octave, start_beat=(c+3*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_arpeggios += add_note(note=note + 12*(octave-1), start_beat=(c+3*octave)*nl, length_in_beats=nl) # Left hand

                # Left Right Alternating
                all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(4*c+12*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_lh_alternating += add_note(note=second_note + 12*octave, start_beat=(2*(4*c+1+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note + 12*octave, start_beat=(2*(4*c+2+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=note + 12*(1+octave), start_beat=(2*(4*c+3+12*octave)+1)*nl, length_in_beats=nl)

                all_notes_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=(2*(4*c+12*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=(2*(4*c+1+12*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=(2*(4*c+2+12*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(4*c+3+12*octave))*nl, length_in_beats=nl)

                # Alternating Left Right Alternating
                all_notes_alternating_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(4*c+12*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating_lh_alternating += add_note(note=second_note + 12*octave, start_beat=(2*(4*c+2+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note + 12*octave, start_beat=(2*(4*c+1+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=note + 12*(1+octave), start_beat=(2*(4*c+3+12*octave)+1)*nl, length_in_beats=nl)

                all_notes_alternating_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=(2*(4*c+12*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_alternating_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=(2*(4*c+2+12*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=(2*(4*c+1+12*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(4*c+3+12*octave))*nl, length_in_beats=nl)

                # Arpeggios Left Right Alternating
                all_notes_arpeggios_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(c+3*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_arpeggios_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=(2*(c+3*octave))*nl, length_in_beats=nl) # Left hand

            note += i
        makefile(all_notes, savedir, '{}_{}_{}'.format(chord, key, nlk))
        makefile(all_notes_broken, savedir, '{}_{}_{}_broken'.format(chord, key, nlk))
        makefile(all_notes_alternating, savedir, '{}_{}_{}_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios, savedir, '{}_{}_{}_arpeggio'.format(chord, key, nlk))
        makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating.'.format(chord, key, nlk))
        makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_{}_lh_alternating_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_{}_lh_arpeggios_alternating'.format(chord, key, nlk))
    return None 

def gen_dec_triads(run, savedir, key, nlk, nl, num_octaves_scale):
    if run==False:
        return False
    
    major_chord_semitones_dec = [-5, -3, -4]
    minor_chord_semitones_dec = [-5, -4, -3]

    chords_dec = {"major_chord_dec": major_chord_semitones_dec, "minor_chord_dec": minor_chord_semitones_dec}

    for chord in chords_dec:
        all_notes = []
        all_notes_broken = []
        all_notes_alternating = []
        all_notes_arpeggios = []
        all_notes_lh_alternating = []
        all_notes_alternating_lh_alternating = []
        all_notes_arpeggios_lh_alternating = []
        note = key
        for c, i in enumerate(chords_dec[chord]): # Iterate over all starting keys of the chords
            second_note = note + chords_dec[chord][c%3]
            third_note = second_note + chords_dec[chord][(c+1)%3]
            for octave in range(num_octaves_chord):
                # Solid
                all_notes += add_chord(notes=[note - 12*octave, second_note - 12*octave, third_note - 12*octave, note - 12*(1+octave)], 
                                       start_beat=(c+3*octave)*nl, length_in_beats=nl)
                all_notes += add_chord(notes=[note - 12*(octave+1), second_note - 12*(octave+1), third_note - 12*(octave+1), note - 12*(octave+2)], 
                                       start_beat=(c+3*octave)*nl, length_in_beats=nl)

                # Broken
                all_notes_broken += add_note(note=note - 12*octave, start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_broken += add_note(note=second_note - 12*octave, start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note - 12*octave, start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=note - 12*(1+octave), start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                all_notes_broken += add_note(note=note - 12*(octave+1), start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_broken += add_note(note=second_note - 12*(octave+1), start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note - 12*(octave+1), start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=note - 12*(octave+2), start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                # Alternating
                all_notes_alternating += add_note(note=note - 12*octave, start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating += add_note(note=second_note - 12*octave, start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note - 12*octave, start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=note - 12*(1+octave), start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                all_notes_alternating += add_note(note=note - 12*(octave+1), start_beat=(4*c+12*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_alternating += add_note(note=second_note - 12*(octave+1), start_beat=(4*c+2+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note - 12*(octave+1), start_beat=(4*c+1+12*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=note - 12*(octave+2), start_beat=(4*c+3+12*octave)*nl, length_in_beats=nl)

                # Arpeggios
                all_notes_arpeggios += add_note(note=note - 12*octave, start_beat=(c+3*octave)*nl, length_in_beats=nl)
                all_notes_arpeggios += add_note(note=note - 12*(octave+1), start_beat=(c+3*octave)*nl, length_in_beats=nl)

                # Left Right Alternating
                all_notes_lh_alternating += add_note(note=note - 12*octave, start_beat=(2*(4*c+12*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_lh_alternating += add_note(note=second_note - 12*octave, start_beat=(2*(4*c+1+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note - 12*octave, start_beat=(2*(4*c+2+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=note - 12*(1+octave), start_beat=(2*(4*c+3+12*octave)+1)*nl, length_in_beats=nl)

                all_notes_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=(2*(4*c+12*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=(2*(4*c+1+12*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=(2*(4*c+2+12*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=note - 12*(octave+2), start_beat=(2*(4*c+3+12*octave))*nl, length_in_beats=nl)

                # Alternating Left Right Alternating
                all_notes_alternating_lh_alternating += add_note(note=note - 12*octave, start_beat=(2*(4*c+12*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating_lh_alternating += add_note(note=second_note - 12*octave, start_beat=(2*(4*c+2+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note - 12*octave, start_beat=(2*(4*c+1+12*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=note - 12*(1+octave), start_beat=(2*(4*c+3+12*octave)+1)*nl, length_in_beats=nl)

                all_notes_alternating_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=(2*(4*c+12*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_alternating_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=(2*(4*c+2+12*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=(2*(4*c+1+12*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=note - 12*(octave+2), start_beat=(2*(4*c+3+12*octave))*nl, length_in_beats=nl)

                # Arpeggios Left Right Alternating
                all_notes_arpeggios_lh_alternating += add_note(note=note - 12*octave, start_beat=(2*(c+3*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_arpeggios_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=(2*(c+3*octave))*nl, length_in_beats=nl) # Left hand
            note += i
        makefile(all_notes, savedir, '{}_{}_{}'.format(chord, key, nlk))
        makefile(all_notes_broken, savedir, '{}_{}_{}_broken'.format(chord, key, nlk))
        makefile(all_notes_alternating, savedir, '{}_{}_{}_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios, savedir, '{}_{}_{}_arpeggio'.format(chord, key, nlk))
        makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating'.format(chord, key, nlk))
        makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_{}_lh_alternating_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_{}_lh_arpeggios_alternating'.format(chord, key, nlk))

    return None 

def gen_sevenths(run, savedir, key, nlk, nl, num_octaves_scale):
    if (run == False):
        return False 
    
    dominant_seventh_chord_semitones = [4, 3, 3, 2]
    diminished_seventh_chord_semitones = [3, 3, 3, 3]
    chords_seventh = {"dominant_seventh_chord": dominant_seventh_chord_semitones, 
                      "diminished_seventh_chord": diminished_seventh_chord_semitones}

    # Write ascending chord sevenths for all keys
    for chord in chords_seventh:
        all_notes = []
        all_notes_broken = []
        all_notes_alternating = []
        all_notes_arpeggios = []
        all_notes_lh_alternating = []
        all_notes_alternating_lh_alternating = []
        all_notes_arpeggios_lh_alternating = []
        note = key
        for c, i in enumerate(chords_seventh[chord]): # Iterate over all starting keys of the chords
            second_note = note + chords_seventh[chord][c%4]
            third_note = second_note + chords_seventh[chord][(c+1)%4]
            fourth_note = third_note + chords_seventh[chord][(c+2)%4]
            for octave in range(num_octaves_chord):
                # Solid
                all_notes += add_chord(notes=[note + 12*octave, second_note + 12*octave, third_note + 12*octave, fourth_note + 12*octave], 
                                       start_beat=(c+4*octave)*nl, length_in_beats=nl)
                all_notes += add_chord(notes=[note + 12*(octave-1), second_note + 12*(octave-1), third_note + 12*(octave-1), fourth_note + 12*(octave-1)], 
                                       start_beat=(c+4*octave)*nl, length_in_beats=nl)
        
                # Broken
                all_notes_broken += add_note(note=note + 12*octave, start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_broken += add_note(note=second_note + 12*octave, start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note + 12*octave, start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=fourth_note + 12*octave, start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)
        
                all_notes_broken += add_note(note=note + 12*(octave-1), start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_broken += add_note(note=second_note + 12*(octave-1), start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note + 12*(octave-1), start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=fourth_note + 12*(octave-1), start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)
        
                # Alternating
                all_notes_alternating += add_note(note=note + 12*octave, start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating += add_note(note=second_note + 12*octave, start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note + 12*octave, start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=fourth_note + 12*octave, start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)
        
                all_notes_alternating += add_note(note=note + 12*(octave-1), start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_alternating += add_note(note=second_note + 12*(octave-1), start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note + 12*(octave-1), start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=fourth_note + 12*(octave-1), start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)
        
                # Arpeggios
                all_notes_arpeggios += add_note(note=note + 12*octave, start_beat=(c+4*octave)*nl, length_in_beats=nl)
                all_notes_arpeggios += add_note(note=note + 12*(octave-1), start_beat=(c+4*octave)*nl, length_in_beats=nl)
        
                # Left Right Alternating
                all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(4*c+16*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_lh_alternating += add_note(note=second_note + 12*octave, start_beat=(2*(4*c+1+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note + 12*octave, start_beat=(2*(4*c+2+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=fourth_note + 12*octave, start_beat=(2*(4*c+3+16*octave)+1)*nl, length_in_beats=nl)
        
                all_notes_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=(2*(4*c+16*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=(2*(4*c+1+16*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=(2*(4*c+2+16*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=fourth_note + 12*(octave-1), start_beat=(2*(4*c+3+16*octave))*nl, length_in_beats=nl)
        
                # Alternating Left Right Alternating
                all_notes_alternating_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(4*c+16*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating_lh_alternating += add_note(note=second_note + 12*octave, start_beat=(2*(4*c+2+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note + 12*octave, start_beat=(2*(4*c+1+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=fourth_note + 12*octave, start_beat=(2*(4*c+3+16*octave)+1)*nl, length_in_beats=nl)
        
                all_notes_alternating_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=(2*(4*c+16*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_alternating_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=(2*(4*c+2+16*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=(2*(4*c+1+16*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=fourth_note + 12*(octave-1), start_beat=(2*(4*c+3+16*octave))*nl, length_in_beats=nl)
        
                # Arpeggios Left Right Alternating
                all_notes_arpeggios_lh_alternating += add_note(note=note + 12*octave, start_beat=(2*(c+4*octave)+1)*nl, length_in_beats=nl)
                all_notes_arpeggios_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=(2*(c+4*octave))*nl, length_in_beats=nl)
        
            note += i
        makefile(all_notes, savedir, '{}_{}_{}'.format(chord, key, nlk))
        makefile(all_notes_broken, savedir, '{}_{}_{}_broken'.format(chord, key, nlk))
        makefile(all_notes_alternating, savedir, '{}_{}_{}_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios, savedir, '{}_{}_{}_arpeggio'.format(chord, key, nlk))
        makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating'.format(chord, key, nlk))
        makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_{}_lh_alternating_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_{}_lh_arpeggios_alternating'.format(chord, key, nlk))

    return None 

def gen_sevenths_dec(run, savedir, key, nlk, nl, num_octaves_scale):
    if (run == False):
        return False 
    
    dominant_seventh_chord_semitones_dec = [-2, -3, -3, -4]
    diminished_seventh_chord_semitones_dec = [-3, -3, -3, -3]
    chords_seventh_dec = {"dominant_seventh_chord_dec": dominant_seventh_chord_semitones_dec,
                          "diminished_seventh_chord_dec": diminished_seventh_chord_semitones_dec}

    # Write descending chord sevenths for all keys
    for chord in chords_seventh_dec:
        all_notes = []
        all_notes_broken = []
        all_notes_alternating = []
        all_notes_arpeggios = []
        all_notes_lh_alternating = []
        all_notes_alternating_lh_alternating = []
        all_notes_arpeggios_lh_alternating = []
        note = key
        
        for c, i in enumerate(chords_seventh_dec[chord]): # Iterate over all starting keys of the chords
            second_note = note + chords_seventh_dec[chord][c%4]
            third_note = second_note + chords_seventh_dec[chord][(c+1)%4]
            fourth_note = third_note + chords_seventh_dec[chord][(c+2)%4]
            
            for octave in range(num_octaves_chord):
                # Solid
                all_notes += add_chord(notes=[note - 12*octave, second_note - 12*octave, third_note - 12*octave, fourth_note - 12*octave], 
                                       start_beat=(c+4*octave)*nl, length_in_beats=nl)
                all_notes += add_chord(notes=[note - 12*(octave+1), second_note - 12*(octave+1), third_note - 12*(octave+1), fourth_note - 12*(octave+1)], 
                                       start_beat=(c+4*octave)*nl, length_in_beats=nl)

                # Broken
                all_notes_broken += add_note(note=note - 12*octave, start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_broken += add_note(note=second_note - 12*octave, start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note - 12*octave, start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=fourth_note - 12*octave, start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)

                all_notes_broken += add_note(note=note - 12*(octave+1), start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_broken += add_note(note=second_note - 12*(octave+1), start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=third_note - 12*(octave+1), start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_broken += add_note(note=fourth_note - 12*(octave+1), start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)

                # Alternating
                all_notes_alternating += add_note(note=note - 12*octave, start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating += add_note(note=second_note - 12*octave, start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note - 12*octave, start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=fourth_note - 12*octave, start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)

                all_notes_alternating += add_note(note=note - 12*(octave+1), start_beat=(4*c+16*octave)*nl, length_in_beats=nl) # Left hand
                all_notes_alternating += add_note(note=second_note - 12*(octave+1), start_beat=(4*c+2+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=third_note - 12*(octave+1), start_beat=(4*c+1+16*octave)*nl, length_in_beats=nl)
                all_notes_alternating += add_note(note=fourth_note - 12*(octave+1), start_beat=(4*c+3+16*octave)*nl, length_in_beats=nl)

                # Arpeggios
                all_notes_arpeggios += add_note(note=note - 12*octave, start_beat=(c+4*octave)*nl, length_in_beats=nl)
                all_notes_arpeggios += add_note(note=note - 12*(octave+1), start_beat=(c+4*octave)*nl, length_in_beats=nl)

                # Left Right Alternating
                all_notes_lh_alternating += add_note(note=note - 12*octave, start_beat=(2*(4*c+16*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_lh_alternating += add_note(note=second_note - 12*octave, start_beat=(2*(4*c+1+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note - 12*octave, start_beat=(2*(4*c+2+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=fourth_note - 12*octave, start_beat=(2*(4*c+3+16*octave)+1)*nl, length_in_beats=nl)

                all_notes_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=(2*(4*c+16*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=(2*(4*c+1+16*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=(2*(4*c+2+16*octave))*nl, length_in_beats=nl)
                all_notes_lh_alternating += add_note(note=fourth_note - 12*(octave+1), start_beat=(2*(4*c+3+16*octave))*nl, length_in_beats=nl)

                # Alternating Left Right Alternating
                all_notes_alternating_lh_alternating += add_note(note=note - 12*octave, start_beat=(2*(4*c+16*octave)+1)*nl, length_in_beats=nl) # Right hand
                all_notes_alternating_lh_alternating += add_note(note=second_note - 12*octave, start_beat=(2*(4*c+2+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note - 12*octave, start_beat=(2*(4*c+1+16*octave)+1)*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=fourth_note - 12*octave, start_beat=(2*(4*c+3+16*octave)+1)*nl, length_in_beats=nl)

                all_notes_alternating_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=(2*(4*c+16*octave))*nl, length_in_beats=nl) # Left hand
                all_notes_alternating_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=(2*(4*c+2+16*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=(2*(4*c+1+16*octave))*nl, length_in_beats=nl)
                all_notes_alternating_lh_alternating += add_note(note=fourth_note - 12*(octave+1), start_beat=(2*(4*c+3+16*octave))*nl, length_in_beats=nl)

                # Arpeggios Left Right Alternating
                all_notes_arpeggios_lh_alternating += add_note(note=note - 12*octave, start_beat=(2*(c+4*octave)+1)*nl, length_in_beats=nl)
                all_notes_arpeggios_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=(2*(c+4*octave))*nl, length_in_beats=nl)
            note += i

        makefile(all_notes, savedir, '{}_{}_{}'.format(chord, key, nlk))
        makefile(all_notes_broken, savedir, '{}_{}_{}_broken'.format(chord, key, nlk))
        makefile(all_notes_alternating, savedir, '{}_{}_{}_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios, savedir, '{}_{}_{}_arpeggio'.format(chord, key, nlk))
        makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating'.format(chord, key, nlk))
        makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_{}_lh_alternating_alternating'.format(chord, key, nlk))
        makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_{}_lh_arpeggios_alternating'.format(chord, key, nlk))
    return None 

if __name__ == '__main__':
    # Parameters
    #savedir = '/Users/cnylu/Desktop/PhD/CSC2506/CSC2506_Project/data/Generated MIDI'
    savedir = Path('/Users/sorensabet/Desktop/MSC/CSC2506_Project/data/Generated MIDI/')

    major = savedir / 'major'
    minor = savedir /  'minor'
    
    maj_train = major / 'train'
    maj_train_midi = major / 'train_midi'
    
    maj_test = major / 'test'
    maj_test_midi = major / 'test_midi'
    
    min_train = minor / 'train'
    min_train_midi = minor / 'train_midi'
    
    min_test = minor / 'test'
    min_test_midi = minor / 'test_midi'
    
    dirs = [savedir, major, minor, 
            maj_train, maj_train_midi, maj_test, maj_test_midi, 
            min_train, min_train_midi, min_test, min_test_midi]
    
    # Use numpy random number generation + seed for reproducible train test split 
    np.random.seed(0)
    
    if (os.path.exists(savedir)):
        shutil.rmtree(savedir)
        print('Cleared directory!')
        
    null = [Path(d).mkdir() for d in dirs]
    
    GENERATE_SCALES = True             # VERIFIED (8 tracks*(52 asc keys +20 desc keys))*6 note lengths = 3,456 files
    GENERATE_TRIADS = True             # VERIFIED (14*(52 asc keys + 20 desc keys))*7 note lengths = 7,056 files
    GENERATE_SEVENTHS = True           # VERIFIED (14*(52 asc keys + 20 desc keys))*7 note lengths = 7,056 files 
    GENERATE_MEL_1 = True              # VERIFIED (2*(52 asc keys))*7*6 note lenghts = 4368 files  
    GENERATE_MEL_2 = True              
    GENERATE_CHORD_PROG_1 = True       
    GENERATE_CHORD_PROG_2 = True       
    GENERATE_MEL_TWINKLE = True        
    GENERATE_MEL_HAPPYBDAY = True       
    
    # Total Expected Number of Files: 28,944 files
    
    # More minors because of harmonic, melodic, and minor 
    #    Also, does diminished get considered as a minor? 
    
    # I can combine differente note lengths in left and right hand 
    # I can stagger notes in left and right hand (LROFfset)
    # I can sample from different note lengths randomly inside each MIDI file 
    
    num_octaves_scale = 4
    num_octaves_chord = 4
    num_octaves_sevenths = 4
    key_range = range(21, 73) # Min: 21, Max: 72 (based on setting num_octaves_scale/chord/sevenths=4 and piano size)
    #key_range = range(61, 62)
    dec_key_range = range(88, 68, -1) # Max: 88, Min: 44 (actually 45 but range ignores last value)
    #dec_key_range = range(88, 87, -1)
    nls = {'16th': 0.25,  
           '8th': 0.5,   
           'd8th': 0.75,
           '4th': 1,     
           '2nd': 2,     
           '1st': 4}
    #nls = {'test': 0.25}
    
    # Combining outer loops for efficiency
    num_files_generated = 0
    for key in tqdm(key_range): 
        print('Key: %d' % key)
        for nl in nls.keys():             
            gen_chord_prog_1(GENERATE_CHORD_PROG_1, savedir, key, nl, nls[nl]) # 2 files
            gen_chord_prog_2(GENERATE_CHORD_PROG_2, savedir, key, nl, nls[nl]) # 2 files
            gen_mel_1(GENERATE_MEL_1, savedir, key, nl, nls[nl]) # 2 files
            gen_mel_2(GENERATE_MEL_2, savedir, key, nl, nls[nl]) # 2 files
            gen_mel_twinkle(GENERATE_MEL_TWINKLE, savedir, key, nl, nls[nl]) # 2 files
            gen_mel_happybday(GENERATE_MEL_HAPPYBDAY, savedir, key, nl, nls[nl]) # 2 files
            gen_scales(GENERATE_SCALES, savedir, key, nl, nls[nl], num_octaves_scale) # 8 files
            gen_triads(GENERATE_TRIADS, savedir, key, nl, nls[nl], num_octaves_scale) # 14 files
            gen_sevenths(GENERATE_SEVENTHS, savedir, key, nl, nls[nl], num_octaves_scale) # 14 fiiles
            num_files_generated += (2*6 + 8 + 2*14)
            print('\nNum files generated: %d' % num_files_generated)
    
    # For descending cases 
    for key in tqdm(dec_key_range): 
        print('Dec Key: %d' % key)
        for nl in nls.keys(): 
            gen_dec_scales(GENERATE_SCALES, savedir, key, nl, nls[nl], num_octaves_scale)
            gen_dec_triads(GENERATE_TRIADS, savedir, key, nl, nls[nl], num_octaves_scale)
            gen_sevenths_dec(GENERATE_SEVENTHS, savedir, key, nl, nls[nl], num_octaves_scale)
            num_files_generated += (2*6 + 8 + 2*14)
            print('\nNum files generated: %d' % num_files_generated)


