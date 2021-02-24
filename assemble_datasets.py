import os
import glob  
import shutil
import pandas as pd
from mido import MidiFile
from mido import bpm2tempo
from mido import tempo2bpm 


datadir = "/Users/sorensabet/Desktop/Master's Coursework/CSC2506_Project/Preprocessing/Raw Data" 
os.chdir(datadir)

files = glob.glob(datadir + '/**/*.mid', recursive=True)
files_pd = pd.DataFrame([x.split('Raw Data/')[1] for x in files])
temp = files_pd[0].str.split('/', expand=True)
temp.rename(columns={0: 'dataset', 1: 'subfolder', 2: 'filename'}, inplace=True)
files_pd = files_pd.merge(temp, left_index=True, right_index=True, how='left')
files_pd.rename(columns={0: 'path'}, inplace=True)
files_pd['song_hash'] = pd.util.hash_pandas_object(files_pd['path'])


# Song level information that I want to track 
#   Relative path ofthe song        (DONE)
#   Name of the song                (DONE)
#   Dataset of the song             (DONE) 
#   Subfolder of the song           (DONE)
#   MIDI Type                       (DONE)
#   Length of the song              (DONE)
#   Number of tracks in the song    (DONE)
#   SongHash                        (DONE)

# Track level information that I want to track 
#   Song_hash                       (DONE)
#   Track Number                    (DONE)
#   Track Names                     (DONE)
#   Track text 
#   Track Message Types 
#   Track Keys
#   Track Instruments 

# Message Level Information 
#   Song_hash
#   Track_number 
#   Message Type 
#   Note Information - Velocity 
#   Note Information - Pitch 
#   Note Information - Delta 
#   Note Information - Time in Beats 
#   Note Information - Time in Seconds 
#   Note Information - Absolute Time in Song 
#   Note Information - Length of Note in Seconds 
#   Can add the entire note dictionary, which will track all of this information 

    
song_res = []
track_res = []
msg_res = []

exceptions  = []

for row in files_pd.iterrows():
    
    print('%d: %s' % (row[0], row[1]['path']))
    
    try:
        mid = MidiFile(row[1]['path'], clip=True)
        song_ntracks = len(mid.tracks)
        song_type = mid.type    
        song_len = mid.length
        song_tpb = mid.ticks_per_beat
        song_charset = mid.charset 
        song_dict = {'song_hash': row[1]['song_hash'], 'n_tracks': song_ntracks, 'MIDI_type': song_type,
                  'length(s)': song_len, 'ticks_per_beat': song_tpb, 'charset': song_charset}
    except Exception as e:
        exceptions.append(e)
        print('Problem with file, skipping!')
        continue
    
    # Song Level Information - If the song is correct
    song_res.append(song_dict)
    
    # Track Level Information 
    
    for track_count, track in enumerate(mid.tracks): 
        print('Starting Track %d\n' % track_count)
        track_nmsgs = len(track)
        track_name1 = track.name
        track_name2 = None 
        track_text = None 
        track_len_seconds = None 
        track_msg_types = set()
        track_bpm = None 
        track_tempo = None
        

        # Message level information - Need this to populate some track level info         
        
        for msg_count, msg in enumerate(track): 
            try:            
                if msg.type == 'track_name':
                    track_name2 = msg.name
                
                if msg.type == 'set_tempo':
                    track_tempo = msg.tempo 
                    track_bpm = tempo2bpm(msg.tempo)
            
                msg_dict = msg.dict()
                msg_dict['song_hash'] = row[1]['song_hash']
                msg_dict['track_num'] = track_count 
                msg_dict['type'] = msg.type 
                msg_dict['realtime'] = msg.realtime
                msg_dict['meta'] = msg.is_meta 
            except Exception as ex:
                exceptions.append(ex)
            msg_res.append(msg_dict)
        
        track_dict = {'song_hash': row[1]['song_hash'], 'track_num': track_count, 
                      'track_name1': track_name1, 'track_name2': track_name2,           
                      'track_num_msgs': track_nmsgs,
                      'track_text': track_text, 'track_length(s)': track_len_seconds}
        track_res.append(track_dict)
    
    if row[0] > 100:
        break
    
print('Song level exceptions')
print(str(exceptions))

song_df = pd.DataFrame.from_records(song_res)
track_df = pd.DataFrame.from_records(track_res)
msg_df = pd.DataFrame.from_records(msg_res)

files_pd = files_pd.merge(song_df, left_on=['song_hash'], right_on=['song_hash'], how='left')