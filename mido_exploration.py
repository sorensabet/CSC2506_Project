import os 
from mido import MidiFile

os.chdir("/Users/sorensabet/Desktop/Master's Coursework/CSC2506_Project/Preprocessing")
mid = MidiFile('VampireKillerCV1.mid')

# MIDI file types:
    # 0: Single track: All messages saved in one track
    # 1: Synchronous: All tracks start at the same time 
    # 2: Asynchronous: Each track indepednent of others 

# Looping through tracks:
for track in mid.tracks:
    print(track)
    print(len(track))
    for msg in mid.tracks[0]:
        print(msg)
    print('\n')

# message_numbers = []
# duplicates = []

# for track in mid.tracks:
#     if len(track) in message_numbers:
#         duplicates.append(track)
#     else:
#         message_numbers.append(len(track))

# for track in duplicates:
#     mid.tracks.remove(track)

# mid.save('VampireKillerCV1_dedup.mid')

# Simple exercise # 1: Try separating each track into a separate MIDI file 

# for count, track in enumerate(mid.tracks):
#     nmid = MidiFile()
#     nmid.tracks.append(track)
#     nmid.save('track' + str(count) + '.mid')

msg = mid.tracks[3][100]

for track in mid.tracks:
    for msg in track: 
        if msg.is_realtime:
            print(msg)

# Useful things to track when I extract data 
#   Length of song 
#   Number of tracks 
#   Number of messages in track 
#   Number of unique notes in track 
#   Tempo of tracks 
#   Key of tracks
#   Instrument of tracks 
#   Delta of the note 
#   Timestep of the note in seconds 
#   Length of the note in seconds 
#   What kinds of messages a track has (if no system specific, ignore)
#   Type of MIDIFile (Type 0, 1, or 2)
#   # Total playback time for type 0, 1, or 2 files 
#   Key signature of the song 
#   Other relevant meta_messages associated with each track
#   


# MIDI objects store tracks 
# MIDI tracks store messages 
# MIDI messages are the individual notes, times, and velocities, and channels 
# Mido msg is Python object with methods and attributes 
# Time attribute of messages is the delta time in ticks  
#    Would be good to come up with an algorithm to extract time from MIDI ticks 
#    Would 
# Frozen message are immutable 
# Open a file with MidiFile(filename.mid)
#   Has tracks attribute (list of all tracks)
#      Each track is a list of messages/meta messages 
#      Time attribute of each msg is its delta time 
#      We can save the entire file in memory and modify as we please 
#      # Iterating ovr Midifile object, generates all messages in playback order 
#      Time attribute is # of seconds since last message/start of file 
# 
#   Time attribute:
#       Inside track, it is delta time in ticks, this must be integer 
#       Inside messages from play. it is delta time in seconds 
#       
#       Tempo, BPM reslution: 
#           A beat is the same as a quarter note 
#           Beats are divided into ticks which are smallest unit of time in MIDI 
#           Each message in MIDI has a delta time: says how many ticks since last message 
#           Note off indicated by velocity=0. 
#           Tempo in MIDI given in microseconds per beat 
#           Default tempo is 500,000 microseconds per beat (120 bpm) # Set tempo changes tempo during a song 
#           Helper functions: bpm2tempo(), tempo2bpm(): Convert to and from BPM. Tempo2BPM can be float
#           Converting between TIcks and Seconds 
#               Need to specify BPM and TPB 
#               tick2second(), second2tick() convert b/w ticks and seconds 
#               Integer rounding may be necessary, MIDI files require ticks to be integers 
#               Increaes resolution with more ticks per eat, set MIDIFile.

# Properties of messages 
# channel 
# note 
# time
# type
# velocity 
# is_meta 
# 

# Types of messages: 
    # Channel messages: Turn notes on/off, change patches, change controlleds 16 channels in each track 
    # System common messages: 
    # System realtime messages (start, stop, continue, song position, reset)
    # System exclusive messages (Sysex messages) 

# Meta Message Types 
    # Track name 
    # Instrument Name 
    # Lyrics 
    # Time Signature 
    
# Library Reference
    # There is a MIDI parser object that can parse a file 

#







