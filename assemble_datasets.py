import os
import glob  
import random
import shutil
import pandas as pd

from mido import MidiFile
from mido import MidiTrack
from mido import bpm2tempo
from mido import tempo2bpm 
from mido import Message
from mido import MetaMessage


datadir = r"C:\Users\Darth\Desktop\CSC2506_Project\Raw Data" 
os.chdir(datadir)

files = glob.glob(datadir + '\**\*.mid', recursive=True)
files_pd = pd.DataFrame([x.split('Raw Data\\')[1] for x in files])
temp = files_pd[0].str.split('\\', expand=True)
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

ignore_types = {'copyright', 'midi_port', 'sequencer_specific', 'sysex', 
                'device_name', 'lyrics', 'cue_marker', 'sequence_number',
                'unknown_meta', 'text'} # Need to experiment with what happens to the song when I remove these types 
msg_keep_types = {'end_of_track', 'program_change', 'control_change',
                  'note_on', 'note_off', 'pitchwheel', 'channel_prefix', 'aftertouch',
                  'polytouch', 'stop', 'set_tempo'}
track_info_types = {'track_name', 'key_signature', 'time_signature', 'marker', 'smpte_offset', 'instrument_name'}

temp_known_types = ignore_types.union(msg_keep_types).union(track_info_types)


for row in files_pd.iterrows():    
    if (row[0] > 10):
        break
   
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
        print('Starting Track %d' % track_count)
        track_orig_nmsgs = len(track)
        track_name = track.name
        track_text = '' 
        track_len_seconds = None 
        track_msg_types = set()
        track_bpm = [] 
        track_tempo = []
        track_key_sig = []
        track_time_sig = []
        track_time_sig_cpc = []
        track_time_sig_n32nd = []
        track_markers = []
        track_smpte = None
        track_inst_name = None
        track_has_pitchwheel = False
        track_new_msg_counter = 0
        
        # Message level information - Need this to populate some track level info         
        
        
        for msg_count, msg in enumerate(track):
            
            # if (msg.type !='pitchwheel'):
            #     continue 
            # else:
            #     print(msg.dict())
            #     input('Batman')
            
            
            # if (msg.type in temp_known_types):
            #     continue
            # These properties will always be defined, so we can always store them.  
            msg_dict = {}
            msg_dict['count'] = msg_count
            msg_dict['type'] = msg.type
            msg_dict['song_hash'] = row[1]['song_hash']
            msg_dict['track_num'] = track_count 
            # msg_dict['realtime'] = msg.is_realtime
            msg_dict['meta'] = msg.is_meta 
            msg_dict['time'] = 0  # Assume time is 0 and then update later
            track_msg_types.add(msg.type)
            
            if (msg.type in track_info_types):
                if (msg.type == 'track_name'):
                    track_name += ' - ' + msg.name
                elif (msg.type == 'key_signature'):
                    track_key_sig.append(msg.key)
                elif (msg.type == 'text'):
                    track_text += msg.text
                elif (msg.type == 'time_signature'):
                    track_time_sig.append(str(msg.numerator) + '/' + str(msg.denominator))
                    track_time_sig_cpc.append(msg.clocks_per_click)
                    track_time_sig_n32nd.append(msg.notated_32nd_notes_per_beat)
                elif (msg.type == 'marker'):
                    track_markers.append(msg.text)      
                elif (msg.type == 'smpte_offset'):
                    temp_dict = msg.dict()
                    del temp_dict['type']
                    track_smpte = temp_dict
                elif (msg.type =='instrument_name'):
                    track_inst_name = msg.name
                continue 
            elif (msg.type in ignore_types):
                continue
            
            if (msg.type == 'set_tempo'):
                track_tempo.append(msg.tempo)
                track_bpm.append(tempo2bpm(msg.tempo))
                            
            msg_res.append({**msg_dict, **msg.dict()})
            track_new_msg_counter += 1

        
        track_dict = {'song_hash': row[1]['song_hash'], 'track_num': track_count, 
                      'track_orig_num_msgs': track_orig_nmsgs, 'track_new_num_msgs': track_new_msg_counter,
                      'track_name': track_name, 
                      'track_tempo(s)': track_tempo, 'track_bpm(s)': track_bpm, 
                      'track_key(s)': track_key_sig, 'track_time_sig(s)': track_time_sig,
                      'track_time_sig_cpc(s)': track_time_sig_cpc, 
                      'track_time_sig_n32nd(s)': track_time_sig_n32nd,
                      'track_marker(s)': track_markers, 
                      'track_smpte': track_smpte, 'track_instrument_name': track_inst_name,
                      'track_msg_types': track_msg_types, 'track_has_pitchwheel': track_has_pitchwheel,
                      #'track_text': track_text, 
                      #'track_length_seconds': track_len_seconds,

                      }
        track_res.append(track_dict)
    
    
print('Song level exceptions')
print(str(exceptions))

song_df = pd.DataFrame.from_records(song_res)
track_df = pd.DataFrame.from_records(track_res)
msg_df = pd.DataFrame.from_records(msg_res)

files_pd = files_pd.merge(song_df, left_on=['song_hash'], right_on=['song_hash'], how='left')

# Okay. Experiment. Copy 10 songs and write the new, reassembled versions to disk.
# See if The MIDI files sound the same as before. 

exp_path = r"C:\Users\Darth\Desktop\CSC2506_Project\MIDI_reconstruction_experiment"
if os.path.exists(exp_path):
    shutil.rmtree(exp_path)
os.mkdir(exp_path)

def make_message(params):
    msg_type = msg[1]['type']
    msg_time = int(msg[1]['time'])


def convert_to_midi(t_df, m_df):
    """
        t_df: Track dataframe
        m_df: Message dataframe
    """
    
    mid = MidiFile()
    for track in t_df.iterrows():
        curr_track = MidiTrack()
        msgs = m_df.loc[m_df['track_num'] == track[1]['track_num']]
        for msg in msgs.iterrows():
            params = {}
            msg_type = msg[1]['type']
            msg_time = int(msg[1]['time'])
            
            #print('params: %s' % str(msg[1]))    
            
            # Logic for re-assembling messages
            if (msg[1]['meta'] is True):      
                if (msg_type == 'set_tempo'):
                    nm = MetaMessage('set_tempo', 
                                     time=msg_time, 
                                     tempo=int(msg[1]['tempo']))
                elif (msg_type == 'end_of_track'):
                    nm = MetaMessage('end_of_track',
                                     time=msg_time)
                elif (msg_type == 'channel_prefix'):
                    nm = MetaMessage(msg_type, 
                                     time=msg_time, 
                                     channel=int(msg[1]['channel']))
                
            else:
                if (msg_type == 'control_change'):
                    nm = Message(msg_type, 
                                 time=msg_time, 
                                 channel=int(msg[1]['channel']),
                                 control=int(msg[1]['control']),
                                 value=int(msg[1]['value']))
                elif (msg_type == 'program_change'):
                    nm = Message(msg_type,
                                 time=msg_time, 
                                 program=int(msg[1]['program']),
                                 channel=int(msg[1]['channel']))
                elif (msg_type == 'note_on' or msg_type == 'note_off'):
                    nm = Message(msg_type, 
                                 time=msg_time, 
                                 channel=int(msg[1]['channel']),
                                 note=int(msg[1]['note']),
                                 velocity=int(msg[1]['velocity']))
                elif (msg_type == 'polytouch'):
                    nm = Message(msg_type, 
                                 time=msg_time, 
                                 channel=int(msg[1]['channel']),
                                 note=int(msg[1]['note']),
                                 value=int(msg[1]['value']))
                elif (msg_type == 'aftertouch'):
                    nm = Message(msg_type, 
                                 time=msg_time, 
                                 channel=int(msg[1]['channel']),
                                 value=int(msg[1]['value']))
                elif (msg_type == 'pitchwheel'):
                    nm = Message(msg_type, 
                                  time=msg_time, 
                                  channel=int(msg[1]['channel']),
                                  pitch=int(msg[1]['pitch']))
                elif (msg_type == 'stop'):
                    nm = Message(msg_type, 
                                 time=msg_time)
                
            curr_track.append(nm)
        mid.tracks.append(curr_track)
        
    
    # Step 1. Create the mido object                            (DONE)
    # Step 2. Create tracks for the mido object.
    # Step 3. Populate the tracks with the correct messages
    # Step 4. Return the mido object. 
    
    return mid 

for song_idx in random.sample(range(0, len(song_df)), 5):
    file_pd = files_pd.iloc[song_idx]
    MIDI_path = file_pd['path']
    MIDI_name = file_pd['filename']
    song_hash = file_pd['song_hash']

    print('Path: %s' % str(MIDI_path))    

    new_folder = exp_path + '\\' + str(song_idx)
    os.mkdir(new_folder)
    shutil.copy(MIDI_path, new_folder + '\\' + MIDI_name)
    
    # Writing the filtered MIDI to disk
    # Step 4a) Get the relevant columns 
    ttrack_df = track_df.loc[track_df['song_hash'] == song_hash]
    tmsg_df = msg_df.loc[msg_df['song_hash'] == song_hash]
    
    new_mid = convert_to_midi(ttrack_df, tmsg_df)
    mid.save(new_folder + '\\FILTERED_' + MIDI_name)
    
    
    # Step 1. Get the correct rows of files_pdf, track_df, and msg_df (DONE)
    # Step 2. Make a folder for that song                             (DONE)
    # Step 3. Copy the old MIDI over as original                      (DONE)
    # Step 4. Write the filtered MIDI to disk                           
    # Step 5. Compare the original vs. generated songs via audio 
    