# Goal: 
    # Try loading MIDI data 
    # Try storing in pickle object 
    # Try reading object from disk 
    # Try storing inside pandas dataframe 
    # Try saving pandas dataframe to disk 
    # Try loading pandas dataframe 
    
import os 
import io 
import mido 
import pygame
import time as t
from midiutil import MIDIFile
import note_seq
from note_seq.protobuf import music_pb2


# Okay. What do I need to do? 
# Challenge # 1: Playing MIDI file in Python 
# Challenge # 2: Playing NoteSequence in Python

twinkle_twinkle = music_pb2.NoteSequence()
twinkle_twinkle.notes.add(pitch=60, start_time=0.0, end_time=0.5, velocity=80)
twinkle_twinkle.notes.add(pitch=60, start_time=0.5, end_time=1.0, velocity=80)
twinkle_twinkle.notes.add(pitch=67, start_time=1.0, end_time=1.5, velocity=80)
twinkle_twinkle.notes.add(pitch=67, start_time=1.5, end_time=2.0, velocity=80)
twinkle_twinkle.notes.add(pitch=69, start_time=2.0, end_time=2.5, velocity=80)
twinkle_twinkle.notes.add(pitch=69, start_time=2.5, end_time=3.0, velocity=80)
twinkle_twinkle.notes.add(pitch=67, start_time=3.0, end_time=4.0, velocity=80)
twinkle_twinkle.notes.add(pitch=65, start_time=4.0, end_time=4.5, velocity=80)
twinkle_twinkle.notes.add(pitch=65, start_time=4.5, end_time=5.0, velocity=80)
twinkle_twinkle.notes.add(pitch=64, start_time=5.0, end_time=5.5, velocity=80)
twinkle_twinkle.notes.add(pitch=64, start_time=5.5, end_time=6.0, velocity=80)
twinkle_twinkle.notes.add(pitch=62, start_time=6.0, end_time=6.5, velocity=80)
twinkle_twinkle.notes.add(pitch=62, start_time=6.5, end_time=7.0, velocity=80)
twinkle_twinkle.notes.add(pitch=60, start_time=7.0, end_time=8.0, velocity=80) 
twinkle_twinkle.total_time = 8

twinkle_twinkle.tempos.add(qpm=60);

a = note_seq.sequence_proto_to_midi_file(twinkle_twinkle, 'twinkle.mid')


# CREATE MEMORY FILE

# memFile = io.StringIO()
# MyMIDI = MIDIFile(1)
# track = 0
# time = 0
# channel = 0
# pitch = 60
# duration = 1
# volume = 100
# MyMIDI.addTrackName(track, time, 'Sample Track')
# MyMIDI.addTempo(track, time, 120)

# # WRITE A SCALE
# MyMIDI.addNote(track, channel, pitch, time, duration, volume)
# for notestep in [2,2,1,2,2,2,1]:
#     time += duration 
#     pitch += notestep 
#     MyMIDI.addNote(track, channel, pitch, time, duration, volume)
# MyMIDI.writeFile(memFile)

# # PLAYBACK

# pygame.init() 
# pygame.mixer.init() 
# memFile.seek(0)
# pygame.mixer.music.load(memFile)
# pygame.mixer.music.play() 
# while pygame.mixer.music.get_busy():
#     time.sleep(1)



# def play_music(music_file):
#     """
#     stream music with mixer.music module in blocking manner
#     this will stream the sound from disk while playing
#     """
#     clock = pygame.time.Clock()
#     try:
#         pygame.mixer.music.load(music_file)
#         print("Music file %s loaded!" % music_file)
#     except pygame.error:
#         print("File %s not found! (%s)" % (music_file, pygame.get_error()))
#         return
#     pygame.mixer.music.play()
#     while pygame.mixer.music.get_busy():
#         # check if playback has finished
#         clock.tick(30)
#     return None

# def play_file(filename):
#     freq = 44100  # audio CD quality
#     bitsize = -16  # unsigned 16 bit
#     channels = 2  # 1 is mono, 2 is stereo
#     buffer = 1024  # number of samples
#     pygame.mixer.init(freq, bitsize, channels, buffer)

#     # optional volume 0 to 1.0
#     pygame.mixer.music.set_volume(0.8)

#     try:
#         play_music(filename)
#     except KeyboardInterrupt:
#         # if user hits Ctrl/C then exit
#         # (works only in console mode)
#         pygame.mixer.music.fadeout(1000)
#         pygame.mixer.music.stop()
#         raise SystemExit
#     return None

# DONE:   Step 1: Set the working directory 
# Step 2: Load in a MIDI file 
# Step 3: Try playing the MIDI file as is 
# Step 4: Check the data type of the MIDI file 
# Step 5: Try saving the MIDI file as a Python pickle object 
# Step 6: Try loading in MIDI file as Python object 

datadir = "/Users/sorensabet/Desktop/Master's Coursework/CSC2506_Project/Preprocessing/Raw Data/"
test = mido.MidiFile(datadir + 'Classical/bach/bach_846.mid')

#play_file(str(v) + '_notes/' + file + ".mid")
