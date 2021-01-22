from midiutil import MIDIFile
import pygame
import time as t


def play_music(music_file):
    """
    stream music with mixer.music module in blocking manner
    this will stream the sound from disk while playing
    """
    clock = pygame.time.Clock()
    try:
        pygame.mixer.music.load(music_file)
        print "Music file %s loaded!" % music_file
    except pygame.error:
        print "File %s not found! (%s)" % (music_file, pygame.get_error())
        return
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        # check if playback has finished
        clock.tick(30)
    return None

def play_file(filename):
    freq = 44100  # audio CD quality
    bitsize = -16  # unsigned 16 bit
    channels = 2  # 1 is mono, 2 is stereo
    buffer = 1024  # number of samples
    pygame.mixer.init(freq, bitsize, channels, buffer)

    # optional volume 0 to 1.0
    pygame.mixer.music.set_volume(0.8)

    try:
        play_music(filename)
    except KeyboardInterrupt:
        # if user hits Ctrl/C then exit
        # (works only in console mode)
        pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.stop()
        raise SystemExit
    return None

# Defining maj/minor scales
W = 2
H = 1
maj = [W,W,H,W,W,W,H]
nmin = [W,H,W,W,H,W,W]

# MIDI Track Details
track    = 0
channel  = 0
time     = 0   # In beats
duration = 1   # In beats
tempo    = 120  # In BPM
volume   = 100 # 0-127, as per the MIDI standard

# degrees  = [0, 62, 64, 65, 67, 69, 71, 72] # MIDI Note number, C major scale

# version (3 or 8 note version)
v = 8

# 3 note POC on major scale
# i is the MIDI number of the first key, see https://www.researchgate.net/profile/Mickael_Tits/publication/283460243/figure/fig8/AS:614346480685058@1523483023512/88-notes-classical-keyboard-Note-names-and-MIDI-numbers.png
count = 0
for i in range(60, 96):
    notes = [i]
    for j in range(0,v-1):
        notes.append(notes[-1] + maj[j])
    print(notes)

    MyMIDI = MIDIFile(1)  # One track, defaults to format 1 (tempo track # automatically created)
    MyMIDI.addTempo(track, time, tempo)

    for pitch in notes:
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        time = time + 1

    file = 'maj-scale-' + str(v) + '-' + str(i)
    with open(str(v) + '_notes/' + file + ".mid", "wb") as output_file:
        MyMIDI.writeFile(output_file)

    # Plays the file!
    play_file(str(v) + '_notes/' + file + ".mid")
    t.sleep(0.5) # Prevents an error
    if (count > 5):
        break
    count += 1








