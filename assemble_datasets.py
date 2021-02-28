import os
import glob  
import random
import shutil
import pandas as pd

from collections import Counter

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
files_pd.reset_index(drop=True, inplace=True)
files_pd['song_idx'] = files_pd.index

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

# If I want to ignore message types, I have to look at the time value and add the previous time
# to the next message 
ignore_types = {'copyright', 'sequencer_specific', 
                'device_name', 'cue_marker', 'sequence_number',
                'unknown_meta', 'text', 'lyrics', } # Need to experiment with what happens to the song when I remove these types 
msg_keep_types = {'end_of_track', 'program_change', 'control_change',
                  'note_on', 'note_off', 'pitchwheel', 'channel_prefix', 'aftertouch',
                  'polytouch', 'stop', 'set_tempo', 'smpte_offset', 'sysex', 
                  'time_signature', 'key_signature', 'midi_port', }
track_info_types = {'track_name',  'marker', 'instrument_name'}

temp_known_types = ignore_types.union(msg_keep_types).union(track_info_types)

used_types = []
written_types = []
ignored_types = []


curr_song = random.randrange(len(files_pd))
curr_song = 71049

for row in files_pd.iterrows():    
    if (row[0] < curr_song):
        continue 
    if (row[0] > curr_song):
        break
   
    print('%d: %s' % (row[0], row[1]['path']))
    
    try:
        mid = MidiFile(row[1]['path'], clip=True)
        song_ntracks = len(mid.tracks)
        song_type = mid.type    
        song_len = mid.length
        song_tpb = mid.ticks_per_beat
        song_charset = mid.charset 
        song_dict = {'song_idx': row[0], 'n_tracks': song_ntracks, 'MIDI_type': song_type,
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
        
        skipped_time = 0
        
        for msg_count, msg in enumerate(track):
            
            if (msg.type in ignore_types):
                skipped_time += msg.time
                ignored_types.append(msg.type)
                continue
            
            used_types.append(msg.type)
            

            # if (msg.type == 'lyrics'):
            #     print(msg.dict())
            #     print(msg.type)
            #     print(msg.is_meta)
            #     input('Batman')
            
            # These properties will always be defined, so we can always store them.  
            msg_dict = {}
            msg_dict['count'] = msg_count
            msg_dict['type'] = msg.type
            msg_dict['song_idx'] = row[0]
            msg_dict['track_num'] = track_count 
            msg_dict['meta'] = msg.is_meta 
            msg_dict['other'] = None
            track_msg_types.add(msg.type)
            
            if (msg.type in track_info_types):
                if (msg.type == 'track_name'):
                    track_name += ' - ' + msg.name
                elif (msg.type == 'text'):
                    track_text += msg.text   
                elif (msg.type =='instrument_name'):
                    track_inst_name = msg.name
                continue 
            
            # If the message falls under these categories, I don't want to 
            # merge msg.dict() with the msg_dict that I created. 
            # This prevents the keys in the msg.dict() from becoming 
            # columns in the new dataframe. 
            
            # I need to clean up this logic somehow, and ensure that 
            # I correctly assigned skipped_time if I skip a type of message.  
            
            if (msg.type == 'set_tempo'):
                track_tempo.append(msg.tempo)
                track_bpm.append(tempo2bpm(msg.tempo))
                msg_dict['tempo'] = msg.tempo
                
            elif (msg.type == 'smpte_offset'):
                msg_dict['other'] = msg.dict()
                
            elif (msg.type == 'sysex'):
                msg_dict['other'] = msg.dict()
                
            elif (msg.type == 'time_signature'):
                track_time_sig.append(str(msg.numerator) + '/' + str(msg.denominator))
                track_time_sig_cpc.append(msg.clocks_per_click)
                track_time_sig_n32nd.append(msg.notated_32nd_notes_per_beat)
                msg_dict['other'] = msg.dict()
                
            elif (msg.type == 'key_signature'):
                track_key_sig.append(msg.key)
                msg_dict['other'] = msg.dict()
                
            elif (msg.type == 'midi_port'):
                msg_dict['other'] = msg.dict()
                
            elif (msg.type == 'lyrics'):
                msg_dict['other'] = msg.dict()
                
            else: 
                msg_dict = {**msg_dict, **msg.dict()}

            # If we skipped any message times, we need to add the time
            # to the next message, otherwise the sequence is messed up
            
            if ('time' in msg_dict):
                msg_dict['time'] += skipped_time
            else:
                msg_dict['time'] = skipped_time
                
            msg_res.append(msg_dict)
            track_new_msg_counter += 1
            skipped_time = 0

        
        track_dict = {'song_idx': row[0], 'song_name': row[1]['filename'],'track_num': track_count, 
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
    
    
# print('Song level exceptions')
# print(str(exceptions))


song_df = pd.DataFrame.from_records(song_res)
track_df = pd.DataFrame.from_records(track_res)
msg_df = pd.DataFrame.from_records(msg_res)

files_pd = files_pd.merge(song_df, left_on=['song_idx'], right_on=['song_idx'], how='left')

# Okay. Experiment. Copy 10 songs and write the new, reassembled versions to disk.
# See if The MIDI files sound the same as before. 

exp_path = r"C:\Users\Darth\Desktop\CSC2506_Project\MIDI_reconstruction_experiment"
if os.path.exists(exp_path):
    shutil.rmtree(exp_path)
os.mkdir(exp_path)

written_types = {}

def convert_to_midi(t_df, m_df, params):
    """
        t_df: Track dataframe
        m_df: Message dataframe
    """
    
    mid = MidiFile(**params)
    
    for track in t_df.iterrows():
        curr_track = MidiTrack()
        msgs = m_df.loc[m_df['track_num'] == track[1]['track_num']]
        
        for msg in msgs.iterrows():
            msg_type = msg[1]['type']
            msg_time = int(msg[1]['time'])
            
           
            # Logic for re-assembling messages
            if (msg[1]['meta'] is True):      
                if (msg_type == 'set_tempo'):
                    nm = MetaMessage('set_tempo', 
                                     time=msg_time, 
                                     tempo=int(msg[1]['tempo']))
                    
                    # print(msg[1])
                    # print(nm)
                    # input('Press enter to continue')
                    
                elif (msg_type == 'end_of_track'):
                    nm = MetaMessage('end_of_track',
                                     time=msg_time)
                elif (msg_type == 'channel_prefix'):
                    nm = MetaMessage(msg_type, 
                                     time=msg_time, 
                                     channel=int(msg[1]['channel']))
                elif (msg_type == 'smpte_offset'):
                    nm = MetaMessage(msg_type, 
                                     frame_rate=msg[1]['other']['frame_rate'],
                                     hours=msg[1]['other']['hours'],
                                     minutes=msg[1]['other']['minutes'],
                                     seconds=msg[1]['other']['seconds'],
                                     frames=msg[1]['other']['frames'],
                                     sub_frames=msg[1]['other']['sub_frames'],
                                     time=msg_time)
                elif (msg_type == 'time_signature'):
                    nm = MetaMessage(msg_type, 
                                     time=msg_time,
                                     numerator=msg[1]['other']['numerator'],
                                     denominator=msg[1]['other']['denominator'],
                                     clocks_per_click=msg[1]['other']['clocks_per_click'],
                                     notated_32nd_notes_per_beat=msg[1]['other']['notated_32nd_notes_per_beat'])
                elif (msg_type == 'key_signature'):
                    nm = MetaMessage(msg_type, 
                                     time=msg_time,
                                     key=msg[1]['other']['key'])
                elif (msg_type == 'midi_port'):
                    nm = MetaMessage(msg_type, 
                                     time=msg_time,
                                     port=msg[1]['other']['port'])
                elif (msg_type == 'lyrics'):
                    nm = MetaMessage(msg_type, 
                                     time=int(msg[1]['other']['time']), 
                                     text=msg[1]['other']['text'])
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
                elif (msg_type == 'sysex'):
                    nm = Message(msg_type, 
                                 time=msg_time,
                                 data=msg[1]['other']['data'])
                
            curr_track.append(nm)
            if (nm.type in written_types):
                written_types[nm.type] += 1
            else:
                written_types[nm.type] = 1
            
        mid.tracks.append(curr_track)
        
    
    # Step 1. Create the mido object                            (DONE)
    # Step 2. Create tracks for the mido object.
    # Step 3. Populate the tracks with the correct messages
    # Step 4. Return the mido object. 
    
    return mid 

song_pd = song_df.merge(files_pd[['song_idx', 'path', 'filename']], on=['song_idx'], how='left')

for song in song_pd.sample(frac=1, random_state=0).iterrows():

    MIDI_path = song[1]['path']
    MIDI_name = song[1]['filename']
    song_idx = song[1]['song_idx']
    
    midi_params = {}
    midi_params['ticks_per_beat'] = song[1]['ticks_per_beat']
    midi_params['type'] = song[1]['MIDI_type']
    
    # print(song_idx)
    # print('MIDI_path: %s' % MIDI_path)
    # print('MIDI_name: %s' % MIDI_name)

    new_folder = exp_path + '\\' + str(song[0])
    os.mkdir(new_folder)
    shutil.copy(MIDI_path, new_folder + '\\' + MIDI_name)
    
    # Writing the filtered MIDI to disk
    # Step 4a) Get the relevant columns 
    ttrack_df = track_df.loc[track_df['song_idx'] == song[1]['song_idx']]
    tmsg_df = msg_df.loc[msg_df['song_idx'] == song[1]['song_idx']]
    
    new_mid = convert_to_midi(ttrack_df, tmsg_df, midi_params)
    new_mid.save(new_folder + '\\FILTERED_' + MIDI_name)
    

    # Okay. I basically need to figure out what I missed.
    # Probably some track level information 
    
    #print('Batman')
    # Step 1. Get the correct rows of files_pdf, track_df, and msg_df (DONE)
    # Step 2. Make a folder for that song                             (DONE)
    # Step 3. Copy the old MIDI over as original                      (DONE)
    # Step 4. Write the filtered MIDI to disk                           
    # Step 5. Compare the original vs. generated songs via audio 


print('Ignored types: ')
print(Counter(ignored_types))

print('Used Types: ')
print(Counter(used_types))

print('Written Types: ')
print(written_types)
