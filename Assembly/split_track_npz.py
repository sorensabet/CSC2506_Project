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
#pd.options.mode.chained_assignment = None

# min_pitch: 
# max_pitch: 
# Homework: Get results for 1k files 

os.chdir("/Users/sorensabet/Desktop/Master's Coursework/CSC2506_Project")

# Read in hdf5 versions of data
song_df = pd.read_json('Dataframes/song_df.json')
track_df = pd.read_json('Dataframes/track_df.json')
msg_df = pd.read_hdf('Dataframes/msg_df.h5', key='data')

# song_df
song_df = song_df.loc[~song_df['ticks_per_beat'].isnull()]
song_df.index = song_df['song_idx']

# track_df
track_df.drop(columns={'song_name','track_has_pitchwheel', 'track_smpte'}, inplace=True)
track_df = track_df.loc[track_df['track_msg_types'].astype(str).str.contains('note') == True][['song_idx', 'track_num']] # Exclude tracks that don't contain notes
track_df.drop_duplicates(subset=['song_idx', 'track_num'],inplace=True)

# msg_df
msg_df = msg_df.loc[msg_df['song_idx'].isin(song_df['song_idx'].unique())]

def split_tracks(tdf, mdf, n_meas=4, n_copies=1, n_transpose=0, merge_tracks=False, song_tpb=480, song_idx= 0, folder=None):
    """
    tdf:           Track level dataframe, contains information about the track 
    mdf:           Message level dataframe, contains information about MIDI messages 
    n_measures:    The number of measures that will form an input to the GAN 
    n_duplicates:      The number of times the track should be duplicated 
    n_transpose:   The number of times the track should be transposed 
    transpose:     True if the MIDI data should be transposed, and number of octaves up and down 
    song_tpb:      The ticks per beat defined in the original song. This is needed to ensure the time values formed mean something. 
    """   
    
    tracks = list(tdf['track_num'].unique())
        
    # Testing Transposing up and down from middle octave
    if (n_transpose > 0):
        print('Transposing!')
        mdf.reset_index(drop=True, inplace=True)
        mdf['note'] = mdf['note'] % 12 + 60     # 60 corresponds to middle C; this preserves notes but might alter harmonics
            
        # Bound the number of transposes to the MIDI range 
        if (n_transpose > 5):
            n_transpose = 5
        if (n_transpose < 0):
            n_transpose = 0

        # For each note, tranpose n times up and down relative to middle C. Since we need middle C to be first:
        ranges = [0] + [n for n in range(n_transpose*(-1), 0)] + [n for n in range(1, n_transpose+1)]
        
        nrs = [{'type': x[1], 'song_idx': x[2], 'track_num': x[3], 'time': x[4] if n == 0 else 0, 
                'velocity': x[5], 'note': x[6] + n*12, 'ctime': x[7], 'cbeats': x[8], 'bar': x[9], 
                } for x in mdf.itertuples() for n in ranges]
        mdf = pd.DataFrame.from_records(nrs)    
        mdf = mdf.loc[mdf['note'].between(0,127)]
        
    if (merge_tracks == True): 
        print('Merging!')

        # Okay. What's the functionality to combine tracks together? 
        mdf.sort_values(by=['cbeats', 'track_num'], inplace=True)
        mdf.reset_index(drop=True, inplace=True)
        mdf['tmp_idx'] = mdf.index

        mdf2 = mdf[['cbeats']].rename(columns={'cbeats': 'prev_row_cbeats'})
        mdf2['tmp_idx'] = mdf2.index + 1

        mdf = mdf.merge(mdf2, on=['tmp_idx'], how='left')
        mdf.fillna({'prev_row_cbeats': 0}, inplace=True)
        mdf['beat_delta'] = mdf['cbeats'] - mdf['prev_row_cbeats']
        mdf['time'] = (mdf['beat_delta']*song_tpb)
        mdf = mdf.round({'time': 0})
        mdf['time'] = mdf['time'].astype(int)
        mdf['track_num'] = 1
        tracks = [1]
    
    mdf = mdf.loc[mdf['type'].isin(['note_on', 'note_off'])]
    mdf['type'] = np.where(mdf['velocity'] == 0, 'note_off', mdf['type']) # Change type to note off
    mdf['outfile'] = (mdf['bar']/n_meas).astype(int)
    midi_type = 1 if n_copies >= 1 else 0
    
    
    for t in tracks:        
        for f in mdf['outfile'].unique():
            #print('Track: %d, Section: %d' % (t,f))
            
            # Create the track specific MIDI file 
            mid = MidiFile(ticks_per_beat=int(song_tpb), type=midi_type)
            midiTrack = MidiTrack()
            
            # Get Specific messages for the track
            tmdf = mdf.loc[(mdf['track_num'] == t) & (mdf['outfile'] == f)]
                      
            # Get relevant information 
            is_empty = len(tmdf) == 0
            no_note_on = len(tmdf.loc[tmdf['type'] == 'note_on']) == 0
            
            # Skip file if there are no notes played in this track
            if (is_empty or no_note_on):
                continue 

            # Tempo MIDI Message
            midiTrack.append(MetaMessage('set_tempo', time=0, tempo=500000))

            # Time Signature MIDI Message (Standardize to 120bpm)
            midiTrack.append(MetaMessage('time_signature', time=0, numerator=4, denominator=4, 
                                         clocks_per_click=24, notated_32nd_notes_per_beat=8))

            # Key Signature MIDI Message (Shouldn't matter since MIDI note number determines the correct note)
            midiTrack.append(MetaMessage('key_signature', time=0, key='C'))
            
            # Individual Messages corresponding to notes 
            midiTrack += [Message(x[1], time=int(x[4]), note=int(x[6]), velocity=int(x[5]), channel=0) for x in tmdf.itertuples()]
            
            # End of Track MIDI Message
            midiTrack.append(MetaMessage('end_of_track', time=0))
            
            # If we want to duplicate the track 
            for i in range(0, n_copies+1):
                mid.tracks.append(midiTrack)
            filename =  folder + str(song_idx) + '_' + str(t) + '_' + str(f) + '.mid' 
            filename_npz = folder + str(song_idx) + '_' + str(t) + '_' + str(f) + '.npz' 
            
            # Save MIDI and NPZ File
            mid.save(filename)
            
            if (is_empty or no_note_on):
                print('Filename: %s' % filename)
                print('Error! No notes found in track, continuing')
                print(tmdf)
                print(mdf['outfile'].unique())
            
            try:
                pyp_mid = pypianoroll.read(filename)
                pyp_mid.save(filename_npz)
            except Exception as ex:
                print(ex)
                print('Error! Currfile: %s' % filename)
                continue
                
n_meas = 16
n_copies = 0
n_transpose = 0
merge_tracks = False 

outpath = "/Users/sorensabet/Desktop/Master's Coursework/CSC2506_Project/Splitting MIDI Files/"
if os.path.exists(outpath):
    shutil.rmtree(outpath)
os.mkdir(outpath)

for song in tqdm(song_df.itertuples()):
    
    song_tpb = song[9] # Ticks per beat 
    
    t_df = track_df.loc[track_df['song_idx'] == song[0]]
    m_df = msg_df.loc[(msg_df['song_idx'] == song[0]) & (msg_df['track_num'].isin(t_df['track_num']))]
    
    new_m_dfs = [] 
    for t in t_df['track_num']:
        temp_msgs = m_df.loc[m_df['track_num'] == t]
        temp_msgs['ctime'] = temp_msgs['time'].cumsum()
        temp_msgs['cbeats'] = temp_msgs['ctime']/song_tpb
        new_m_dfs.append(temp_msgs)
    
    if (len(new_m_dfs) == 0):
        continue
    
    m_df = pd.concat(new_m_dfs)
    m_df['bar'] = (m_df['cbeats']/4).astype(int)  

    # Step 1. Copy original song over to the new folder 
    # Step 2. Write all split files into the new folder 
    
    orig_path = song[1]
    song_folder = outpath + str(song[0]) + '/'
    os.mkdir(song_folder)
    
    shutil.copy('Raw Data/' + orig_path, song_folder + str(song[0]) +'_original.midi')

    split_tracks(t_df, m_df, n_meas=n_meas, n_copies=n_copies, n_transpose=n_transpose, merge_tracks=merge_tracks, song_tpb=song_tpb, song_idx=song[0], folder=song_folder)

# mid = MidiFile("/Users/sorensabet/Desktop/Master's Coursework/CSC2506_Project/Splitting MIDI Files/23/23_10_0.mid")
# for msg in mid.tracks[0]:
#     print(msg)
    
# Objective 1: Successfully generate NPZ files for all MIDI files being split