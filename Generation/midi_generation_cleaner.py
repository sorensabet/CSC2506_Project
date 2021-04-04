import os 
import sys
import shutil
import numpy as np
import pandas as pd
from mido import Message, MidiFile, MidiTrack, bpm2tempo, tempo2bpm, MetaMessage

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
    df['ctime'] = df['start_beat']*480                                         # Use 480 ticks per beat 
    df['time'] = df['ctime'] - df['ctime'].shift(1)                            # MIDI commands are sequential, we need to go from cumulative time to time between events
    df = df[['type', 'note', 'time', 'start_beat', 'ctime']].fillna(0)
    df = df.astype({'type': 'category', 'time': int, 
                    'start_beat': float, 'ctime': float})
    df['velocity'] = np.where(df['type'] == 'note_on', 64, 0)
        
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
    
    # Individual Messages corresponding to notes 
    midiTrack += [Message(x[1],  note=int(x[2]), time=int(x[3]), velocity=int(x[6]), channel=0) for x in df.itertuples()]
    
    # End of Track MIDI Message
    midiTrack.append(MetaMessage('end_of_track', time=0))
    
    # Append Track to MIDI File
    mid.tracks.append(midiTrack)

    mid.save(savedir + '/' + filename)
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
        makefile(all_notes, savedir, '{}_{}_{}_CHORD_PROG_1.mid'.format(scale, key, nlk))
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
        makefile(all_notes, savedir, '{}_{}_{}_CHORD_PROG_2.mid'.format(scale, key, nlk))
    return None 

def gen_mel_1(run, savedir, key, nlk, nl):
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
        makefile(all_notes, savedir, '{}_{}_{}_MEL_1.mid'.format(scale, key, nlk))
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
        makefile(all_notes, savedir, '{}_{}_{}_MEL_2.mid'.format(scale, key, nlk))

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
        makefile(all_notes, savedir, '{}_{}_{}_MEL_TWINKLE.mid'.format(scale, key, nlk))
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
        makefile(all_notes, savedir, '{}_{}_{}_MEL_HAPPYBDAY.mid'.format(scale, key, nlk))
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
        makefile(all_notes, savedir, '{}_{}_{}.mid'.format(scale, key, nlk))
        makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating.mid'.format(scale, key, nlk))
 
    return None 

def gen_dec_scales(run, savedir, key, nlk, nl, num_octaves_scale):
    
    major_semitones_dec = [-1,-2,-2,-2,-1,-2,-2]
    minor_natural_semitones_dec = [-2,-2,-1,-2,-2,-1,-2]
    minor_harmonic_semitones_dec = [-1,-3,-1,-2,-2,-1,-2]
    minor_melodic_semitones_dec = [-1,-2,-2,-2,-2,-1,-2]

    scales_dec = {"major_scale_dec": major_semitones_dec, "minor_natural_scale_dec": minor_natural_semitones_dec, 
                  "minor_harmonic_scale_dec": minor_harmonic_semitones_dec, "minor_melodic_scale_dec": minor_melodic_semitones_dec}
    
    # Write descending scales for all keys
    for scale in scales_dec:
        for key in dec_key_range: # Iterate over all keys
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
            makefile(all_notes, savedir, '{}_{}_{}.mid'.format(scale, key, nlk))
            makefile(all_notes_lh_alternating, savedir, '{}_{}_{}_lh_alternating.mid'.format(scale, key, nlk))  
    return None 
    
if __name__ == '__main__':
    # Parameters
    #savedir = '/Users/cnylu/Desktop/PhD/CSC2506/CSC2506_Project/data/Generated MIDI'
    savedir = '/Users/sorensabet/Desktop/MSC/CSC2506_Project/data/Generated MIDI'
    
    if (os.path.exists(savedir)):
        shutil.rmtree(savedir)
    os.mkdir(savedir)
    
    GENERATE_SCALES = True
    GENERATE_TRIADS = True
    GENERATE_SEVENTHS = True
    GENERATE_MEL_1 = True
    GENERATE_MEL_2 = True
    GENERATE_CHORD_PROG_1 = True   # MAJ/MIN: C, A, F, G (Also add broken, solid versions)
    GENERATE_CHORD_PROG_2 = True   
    GENERATE_MEL_TWINKLE = True
    GENERATE_MEL_HAPPYBDAY = True
    
    # I can combine differente note lengths in left and right hand 
    # I can stagger notes in left and right hand (LROFfset)
    # I can sample from different note lengths randomly inside each MIDI file 
    
    num_octaves_scale = 1
    num_octaves_chord = 4
    num_octaves_sevenths = 4
    key_range = range(36,84)
    dec_key_range = range(96, 36, -1)
    nls = {'64th': 0.125,'dot_64th': 0.1875,
           '32nd': 0.25, 'dot_32nd': 0.375, 
           '16th': 0.5,  'dot_16th': 0.75,
           '4th': 1,     'dot_4th': 1.5, 
           '2nd': 2,     'dot_2nd': 3, 
           '1st': 4,     'dot_1st': 6}
    LROffset = {} 
    
    # Combining outer loops for efficiency
    for key in key_range: 
        for nl in nls.keys():             
            gen_chord_prog_1(GENERATE_CHORD_PROG_1, savedir, key, nl, nls[nl])
            gen_chord_prog_2(GENERATE_CHORD_PROG_2, savedir, key, nl, nls[nl])
            gen_mel_1(GENERATE_MEL_1, savedir, key, nl, nls[nl])
            gen_mel_2(GENERATE_MEL_1, savedir, key, nl, nls[nl])
            gen_mel_twinkle(GENERATE_MEL_TWINKLE, savedir, key, nl, nls[nl])
            gen_mel_happybday(GENERATE_MEL_HAPPYBDAY, savedir, key, nl, nls[nl])
            gen_scales(GENERATE_SCALES, savedir, key, nl, nls[nl], num_octaves_scale)
            
    # For descending cases 
    for key in dec_key_range: 
        for nl in nls.keys(): 
            gen_dec_scales(GENERATE_SCALES, savedir, key, nl, nls[nl], num_octaves_scale)

    sys.exit()


    if GENERATE_TRIADS:
        # Write major chords for all keys
        major_chord_semitones = [4, 3, 5]
        minor_chord_semitones = [3, 4, 5]
        major_chord_semitones_dec = [-5, -3, -4]
        minor_chord_semitones_dec = [-5, -4, -3]

        chords = {"major_chord": major_chord_semitones, "minor_chord": minor_chord_semitones}
        chords_dec = {"major_chord_dec": major_chord_semitones_dec, "minor_chord_dec": minor_chord_semitones_dec}

        # Write ascending chords for all keys
        for chord in chords:
            for key in key_range: # Iterate over all keys
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
                        all_notes += add_chord(notes=[note + 12*octave, second_note + 12*octave, third_note + 12*octave, note + 12*(1+octave)], start_beat=c+3*octave, length_in_beats=0.5)
                        all_notes += add_chord(notes=[note + 12*(octave-1), second_note + 12*(octave-1), third_note + 12*(octave-1), note + 12*octave], start_beat=c+3*octave, length_in_beats=0.5)

                        # Broken
                        all_notes_broken += add_note(note=note + 12*octave, start_beat=4*c+12*octave, length_in_beats=0.5) # Right hand
                        all_notes_broken += add_note(note=second_note + 12*octave, start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note + 12*octave, start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=note + 12*(1+octave), start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        all_notes_broken += add_note(note=note + 12*(octave-1), start_beat=4*c+12*octave, length_in_beats=0.5) # Left hand
                        all_notes_broken += add_note(note=second_note + 12*(octave-1), start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note + 12*(octave-1), start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=note + 12*octave, start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        # Alternating
                        all_notes_alternating += add_note(note=note + 12*octave, start_beat=4*c+12*octave, length_in_beats=0.5) # Right hand
                        all_notes_alternating += add_note(note=second_note + 12*octave, start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note + 12*octave, start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=note + 12*(1+octave), start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        all_notes_alternating += add_note(note=note + 12*(octave-1), start_beat=4*c+12*octave, length_in_beats=0.5) # Left hand
                        all_notes_alternating += add_note(note=second_note + 12*(octave-1), start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note + 12*(octave-1), start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=note + 12*octave, start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        # Arpeggios
                        all_notes_arpeggios += add_note(note=note + 12*octave, start_beat=c+3*octave, length_in_beats=0.5) # Right hand
                        all_notes_arpeggios += add_note(note=note + 12*(octave-1), start_beat=c+3*octave, length_in_beats=0.5) # Left hand

                        # Left Right Alternating
                        all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(4*c+12*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_lh_alternating += add_note(note=second_note + 12*octave, start_beat=2*(4*c+1+12*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note + 12*octave, start_beat=2*(4*c+2+12*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=note + 12*(1+octave), start_beat=2*(4*c+3+12*octave)+1, length_in_beats=0.5)

                        all_notes_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=2*(4*c+12*octave), length_in_beats=0.5) # Left hand
                        all_notes_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=2*(4*c+1+12*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=2*(4*c+2+12*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(4*c+3+12*octave), length_in_beats=0.5)

                        # Alternating Left Right Alternating
                        all_notes_alternating_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(4*c+12*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note + 12*octave, start_beat=2*(4*c+2+12*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note + 12*octave, start_beat=2*(4*c+1+12*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=note + 12*(1+octave), start_beat=2*(4*c+3+12*octave)+1, length_in_beats=0.5)

                        all_notes_alternating_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=2*(4*c+12*octave), length_in_beats=0.5) # Left hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=2*(4*c+2+12*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=2*(4*c+1+12*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(4*c+3+12*octave), length_in_beats=0.5)

                        # Arpeggios Left Right Alternating
                        all_notes_arpeggios_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(c+3*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_arpeggios_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=2*(c+3*octave), length_in_beats=0.5) # Left hand

                    note += i
                makefile(all_notes, savedir, '{}_{}.mid'.format(chord, key))
                makefile(all_notes_broken, savedir, '{}_{}_broken.mid'.format(chord, key))
                makefile(all_notes_alternating, savedir, '{}_{}_alternating.mid'.format(chord, key))
                makefile(all_notes_arpeggios, savedir, '{}_{}_arpeggio.mid'.format(chord, key))
                makefile(all_notes_lh_alternating, savedir, '{}_{}_lh_alternating.mid'.format(chord, key))
                makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_lh_alternating_alternating.mid'.format(chord, key))
                makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_lh_arpeggios_alternating.mid'.format(chord, key))

        # Write descending chords for all keys
        for chord in chords_dec:
            for key in dec_key_range: # Iterate over all keys
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
                        all_notes += add_chord(notes=[note - 12*octave, second_note - 12*octave, third_note - 12*octave, note - 12*(1+octave)], start_beat=c+3*octave, length_in_beats=0.5)
                        all_notes += add_chord(notes=[note - 12*(octave+1), second_note - 12*(octave+1), third_note - 12*(octave+1), note - 12*(octave+2)], start_beat=c+3*octave, length_in_beats=0.5)

                        # Broken
                        all_notes_broken += add_note(note=note - 12*octave, start_beat=4*c+12*octave, length_in_beats=0.5) # Right hand
                        all_notes_broken += add_note(note=second_note - 12*octave, start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note - 12*octave, start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=note - 12*(1+octave), start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        all_notes_broken += add_note(note=note - 12*(octave+1), start_beat=4*c+12*octave, length_in_beats=0.5) # Left hand
                        all_notes_broken += add_note(note=second_note - 12*(octave+1), start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note - 12*(octave+1), start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=note - 12*(octave+2), start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        # Alternating
                        all_notes_alternating += add_note(note=note - 12*octave, start_beat=4*c+12*octave, length_in_beats=0.5) # Right hand
                        all_notes_alternating += add_note(note=second_note - 12*octave, start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note - 12*octave, start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=note - 12*(1+octave), start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        all_notes_alternating += add_note(note=note - 12*(octave+1), start_beat=4*c+12*octave, length_in_beats=0.5) # Left hand
                        all_notes_alternating += add_note(note=second_note - 12*(octave+1), start_beat=4*c+2+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note - 12*(octave+1), start_beat=4*c+1+12*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=note - 12*(octave+2), start_beat=4*c+3+12*octave, length_in_beats=0.5)

                        # Arpeggios
                        all_notes_arpeggios += add_note(note=note - 12*octave, start_beat=c+3*octave, length_in_beats=0.5)
                        all_notes_arpeggios += add_note(note=note - 12*(octave+1), start_beat=c+3*octave, length_in_beats=0.5)

                        # Left Right Alternating
                        all_notes_lh_alternating += add_note(note=note - 12*octave, start_beat=2*(4*c+12*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_lh_alternating += add_note(note=second_note - 12*octave, start_beat=2*(4*c+1+12*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note - 12*octave, start_beat=2*(4*c+2+12*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=note - 12*(1+octave), start_beat=2*(4*c+3+12*octave)+1, length_in_beats=0.5)

                        all_notes_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=2*(4*c+12*octave), length_in_beats=0.5) # Left hand
                        all_notes_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=2*(4*c+1+12*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=2*(4*c+2+12*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=note - 12*(octave+2), start_beat=2*(4*c+3+12*octave), length_in_beats=0.5)

                        # Alternating Left Right Alternating
                        all_notes_alternating_lh_alternating += add_note(note=note - 12*octave, start_beat=2*(4*c+12*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note - 12*octave, start_beat=2*(4*c+2+12*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note - 12*octave, start_beat=2*(4*c+1+12*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=note - 12*(1+octave), start_beat=2*(4*c+3+12*octave)+1, length_in_beats=0.5)

                        all_notes_alternating_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=2*(4*c+12*octave), length_in_beats=0.5) # Left hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=2*(4*c+2+12*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=2*(4*c+1+12*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=note - 12*(octave+2), start_beat=2*(4*c+3+12*octave), length_in_beats=0.5)

                        # Arpeggios Left Right Alternating
                        all_notes_arpeggios_lh_alternating += add_note(note=note - 12*octave, start_beat=2*(c+3*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_arpeggios_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=2*(c+3*octave), length_in_beats=0.5) # Left hand
                    note += i
                makefile(all_notes, savedir, '{}_{}.mid'.format(chord, key))
                makefile(all_notes_broken, savedir, '{}_{}_broken.mid'.format(chord, key))
                makefile(all_notes_alternating, savedir, '{}_{}_alternating.mid'.format(chord, key))
                makefile(all_notes_broken, savedir, '{}_{}_arpeggio.mid'.format(chord, key))
                makefile(all_notes_lh_alternating, savedir, '{}_{}_lh_alternating.mid'.format(chord, key))
                makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_lh_alternating_alternating.mid'.format(chord, key))
                makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_lh_arpeggios_alternating.mid'.format(chord, key))

    if GENERATE_SEVENTHS:
        dominant_seventh_chord_semitones = [4, 3, 3, 2]
        diminished_seventh_chord_semitones = [3, 3, 3, 3]
        dominant_seventh_chord_semitones_dec = [-2, -3, -3, -4]
        diminished_seventh_chord_semitones_dec = [-3, -3, -3, -3]

        chords_seventh = {"dominant_seventh_chord": dominant_seventh_chord_semitones, "diminished_seventh_chord": diminished_seventh_chord_semitones}
        chords_seventh_dec = {"dominant_seventh_chord_dec": dominant_seventh_chord_semitones_dec, "diminished_seventh_chord_dec": diminished_seventh_chord_semitones_dec}

        # Write ascending chord sevenths for all keys
        for chord in chords_seventh:
            for key in key_range: # Iterate over all keys
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
                        all_notes += add_chord(notes=[note + 12*octave, second_note + 12*octave, third_note + 12*octave, fourth_note + 12*octave], start_beat=c+4*octave, length_in_beats=0.5)
                        all_notes += add_chord(notes=[note + 12*(octave-1), second_note + 12*(octave-1), third_note + 12*(octave-1), fourth_note + 12*(octave-1)], start_beat=c+4*octave, length_in_beats=0.5)

                        # Broken
                        all_notes_broken += add_note(note=note + 12*octave, start_beat=4*c+16*octave, length_in_beats=0.5) # Right hand
                        all_notes_broken += add_note(note=second_note + 12*octave, start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note + 12*octave, start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=fourth_note + 12*octave, start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        all_notes_broken += add_note(note=note + 12*(octave-1), start_beat=4*c+16*octave, length_in_beats=0.5) # Left hand
                        all_notes_broken += add_note(note=second_note + 12*(octave-1), start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note + 12*(octave-1), start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=fourth_note + 12*(octave-1), start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        # Alternating
                        all_notes_alternating += add_note(note=note + 12*octave, start_beat=4*c+16*octave, length_in_beats=0.5) # Right hand
                        all_notes_alternating += add_note(note=second_note + 12*octave, start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note + 12*octave, start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=fourth_note + 12*octave, start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        all_notes_alternating += add_note(note=note + 12*(octave-1), start_beat=4*c+16*octave, length_in_beats=0.5) # Left hand
                        all_notes_alternating += add_note(note=second_note + 12*(octave-1), start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note + 12*(octave-1), start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=fourth_note + 12*(octave-1), start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        # Arpeggios
                        all_notes_arpeggios += add_note(note=note + 12*octave, start_beat=c+4*octave, length_in_beats=0.5)
                        all_notes_arpeggios += add_note(note=note + 12*(octave-1), start_beat=c+4*octave, length_in_beats=0.5)

                        # Left Right Alternating
                        all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(4*c+16*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_lh_alternating += add_note(note=second_note + 12*octave, start_beat=2*(4*c+1+16*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note + 12*octave, start_beat=2*(4*c+2+16*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=fourth_note + 12*octave, start_beat=2*(4*c+3+16*octave)+1, length_in_beats=0.5)

                        all_notes_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=2*(4*c+16*octave), length_in_beats=0.5) # Left hand
                        all_notes_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=2*(4*c+1+16*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=2*(4*c+2+16*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=fourth_note + 12*(octave-1), start_beat=2*(4*c+3+16*octave), length_in_beats=0.5)

                        # Alternating Left Right Alternating
                        all_notes_alternating_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(4*c+16*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note + 12*octave, start_beat=2*(4*c+2+16*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note + 12*octave, start_beat=2*(4*c+1+16*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=fourth_note + 12*octave, start_beat=2*(4*c+3+16*octave)+1, length_in_beats=0.5)

                        all_notes_alternating_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=2*(4*c+16*octave), length_in_beats=0.5) # Left hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note + 12*(octave-1), start_beat=2*(4*c+2+16*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note + 12*(octave-1), start_beat=2*(4*c+1+16*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=fourth_note + 12*(octave-1), start_beat=2*(4*c+3+16*octave), length_in_beats=0.5)

                        # Arpeggios Left Right Alternating
                        all_notes_arpeggios_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(c+4*octave)+1, length_in_beats=0.5)
                        all_notes_arpeggios_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=2*(c+4*octave), length_in_beats=0.5)

                    note += i
                makefile(all_notes, savedir, '{}_{}.mid'.format(chord, key))
                makefile(all_notes_broken, savedir, '{}_{}_broken.mid'.format(chord, key))
                makefile(all_notes_alternating, savedir, '{}_{}_alternating.mid'.format(chord, key))
                makefile(all_notes_broken, savedir, '{}_{}_arpeggio.mid'.format(chord, key))
                makefile(all_notes_lh_alternating, savedir, '{}_{}_lh_alternating.mid'.format(chord, key))
                makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_lh_alternating_alternating.mid'.format(chord, key))
                makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_lh_arpeggios_alternating.mid'.format(chord, key))

        # Write descending chord sevenths for all keys
        for chord in chords_seventh_dec:
            for key in dec_key_range: # Iterate over all keys
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
                        all_notes += add_chord(notes=[note - 12*octave, second_note - 12*octave, third_note - 12*octave, fourth_note - 12*octave], start_beat=c+4*octave, length_in_beats=0.5)
                        all_notes += add_chord(notes=[note - 12*(octave+1), second_note - 12*(octave+1), third_note - 12*(octave+1), fourth_note - 12*(octave+1)], start_beat=c+4*octave, length_in_beats=0.5)

                        # Broken
                        all_notes_broken += add_note(note=note - 12*octave, start_beat=4*c+16*octave, length_in_beats=0.5) # Right hand
                        all_notes_broken += add_note(note=second_note - 12*octave, start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note - 12*octave, start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=fourth_note - 12*octave, start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        all_notes_broken += add_note(note=note - 12*(octave+1), start_beat=4*c+16*octave, length_in_beats=0.5) # Left hand
                        all_notes_broken += add_note(note=second_note - 12*(octave+1), start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=third_note - 12*(octave+1), start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_broken += add_note(note=fourth_note - 12*(octave+1), start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        # Alternating
                        all_notes_alternating += add_note(note=note - 12*octave, start_beat=4*c+16*octave, length_in_beats=0.5) # Right hand
                        all_notes_alternating += add_note(note=second_note - 12*octave, start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note - 12*octave, start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=fourth_note - 12*octave, start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        all_notes_alternating += add_note(note=note - 12*(octave+1), start_beat=4*c+16*octave, length_in_beats=0.5) # Left hand
                        all_notes_alternating += add_note(note=second_note - 12*(octave+1), start_beat=4*c+2+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=third_note - 12*(octave+1), start_beat=4*c+1+16*octave, length_in_beats=0.5)
                        all_notes_alternating += add_note(note=fourth_note - 12*(octave+1), start_beat=4*c+3+16*octave, length_in_beats=0.5)

                        # Arpeggios
                        all_notes_arpeggios += add_note(note=note - 12*octave, start_beat=c+4*octave, length_in_beats=0.5)
                        all_notes_arpeggios += add_note(note=note - 12*(octave+1), start_beat=c+4*octave, length_in_beats=0.5)

                        # Left Right Alternating
                        all_notes_lh_alternating += add_note(note=note - 12*octave, start_beat=2*(4*c+16*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_lh_alternating += add_note(note=second_note - 12*octave, start_beat=2*(4*c+1+16*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note - 12*octave, start_beat=2*(4*c+2+16*octave)+1, length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=fourth_note - 12*octave, start_beat=2*(4*c+3+16*octave)+1, length_in_beats=0.5)

                        all_notes_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=2*(4*c+16*octave), length_in_beats=0.5) # Left hand
                        all_notes_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=2*(4*c+1+16*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=2*(4*c+2+16*octave), length_in_beats=0.5)
                        all_notes_lh_alternating += add_note(note=fourth_note - 12*(octave+1), start_beat=2*(4*c+3+16*octave), length_in_beats=0.5)

                        # Alternating Left Right Alternating
                        all_notes_alternating_lh_alternating += add_note(note=note - 12*octave, start_beat=2*(4*c+16*octave)+1, length_in_beats=0.5) # Right hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note - 12*octave, start_beat=2*(4*c+2+16*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note - 12*octave, start_beat=2*(4*c+1+16*octave)+1, length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=fourth_note - 12*octave, start_beat=2*(4*c+3+16*octave)+1, length_in_beats=0.5)

                        all_notes_alternating_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=2*(4*c+16*octave), length_in_beats=0.5) # Left hand
                        all_notes_alternating_lh_alternating += add_note(note=second_note - 12*(octave+1), start_beat=2*(4*c+2+16*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=third_note - 12*(octave+1), start_beat=2*(4*c+1+16*octave), length_in_beats=0.5)
                        all_notes_alternating_lh_alternating += add_note(note=fourth_note - 12*(octave+1), start_beat=2*(4*c+3+16*octave), length_in_beats=0.5)

                        # Arpeggios Left Right Alternating
                        all_notes_arpeggios_lh_alternating += add_note(note=note - 12*octave, start_beat=2*(c+4*octave)+1, length_in_beats=0.5)
                        all_notes_arpeggios_lh_alternating += add_note(note=note - 12*(octave+1), start_beat=2*(c+4*octave), length_in_beats=0.5)
                    note += i
                makefile(all_notes, savedir, '{}_{}.mid'.format(chord, key))
                makefile(all_notes_broken, savedir, '{}_{}_broken.mid'.format(chord, key))
                makefile(all_notes_alternating, savedir, '{}_{}_alternating.mid'.format(chord, key))
                makefile(all_notes_arpeggios, savedir, '{}_{}_arpeggio.mid'.format(chord, key))
                makefile(all_notes_lh_alternating, savedir, '{}_{}_lh_alternating.mid'.format(chord, key))
                makefile(all_notes_alternating_lh_alternating, savedir, '{}_{}_lh_alternating_alternating.mid'.format(chord, key))
                makefile(all_notes_arpeggios_lh_alternating, savedir, '{}_{}_lh_arpeggios_alternating.mid'.format(chord, key))