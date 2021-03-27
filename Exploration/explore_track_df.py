import os
import time 
import numpy as np
import pandas as pd


os.chdir("/Users/sorensabet/Desktop/Master's Coursework/CSC2506_Project")

song_df = pd.read_json('Raw Data/song_df.json')
track_df = pd.read_json('Raw Data/track_df.json')
msgs_df = pd.read_json('Raw Data/msgs_df.json')

# song_df.to_hdf('Raw Data/song_df.h5', key='data')
# track_df.to_hdf('Raw Data/track_df.h5', key='data')
# msgs_df.to_hdf('Raw Data/msgs_df.h5', key='data')

