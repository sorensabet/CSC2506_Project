### Search for a song that contains a message type

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

for row in files_pd.itertuples():    
    print(row[0])
    if (row[0] < 0):
        continue
    
    try:
        mid = MidiFile(row[1], clip=True)
    except Exception as e:
        continue
    
    for track_count, track in enumerate(mid.tracks): 
        for msg_count, msg in enumerate(track):
            if (msg.type == 'smpte_offset'):
                print(row[0])
                print(msg.dict())
                print(msg.type)
                print(msg.is_meta)
                input('Batman')
            