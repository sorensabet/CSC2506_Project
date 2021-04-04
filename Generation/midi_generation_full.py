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

if __name__ == '__main__':
    # Parameters
    savedir = '/Users/cnylu/Desktop/PhD/CSC2506/CSC2506_Project/data/Generated MIDI'
    GENERATE_SCALES = False
    GENERATE_TRIADS = False
    GENERATE_SEVENTHS = True
    num_octaves_scale = 4
    num_octaves_chord = 4
    num_octaves_sevenths = 4

    if GENERATE_SCALES:
        all_notes = []
        major_semitones = [2,2,1,2,2,2,1]
        minor_natural_semitones = [2,1,2,2,1,2,2]
        minor_harmonic_semitones = [2,1,2,2,1,3,1]
        minor_melodic_semitones = [2,1,2,2,2,2,1]

        major_semitones_dec = [-1,-2,-2,-2,-1,-2,-2]
        minor_natural_semitones_dec = [-2,-2,-1,-2,-2,-1,-2]
        minor_harmonic_semitones_dec = [-1,-3,-1,-2,-2,-1,-2]
        minor_melodic_semitones_dec = [-1,-2,-2,-2,-2,-1,-2]

        scales = {"major_scale": major_semitones, "minor_natural_scale": minor_natural_semitones, "minor_harmonic_scale": minor_harmonic_semitones, "minor_melodic_scale": minor_melodic_semitones}
        scales_dec = {"major_scale_dec": major_semitones_dec, "minor_natural_scale_dec": minor_natural_semitones_dec, 
                      "minor_harmonic_scale_dec": minor_harmonic_semitones_dec, "minor_melodic_scale_dec": minor_melodic_semitones_dec}

        # Write ascending scales for all keys
        for scale in scales:
            for key in range(36, 48): # Iterate over all keys
                all_notes = []
                all_notes_lh_alternating = []
                note = key
                for c, i in enumerate(scales[scale]): # Iterate over all notes within the scale
                    for octave in range(num_octaves_scale):
                        all_notes += add_note(note=note + 12*octave, start_beat=c+7*octave, length_in_beats=0.5) # Right hand
                        all_notes += add_note(note=note + 12*(octave-1), start_beat=c+7*octave, length_in_beats=0.5) # Left hand
                        all_notes_lh_alternating += add_note(note=note + 12*octave, start_beat=2*(c+7*octave) + 1, length_in_beats=0.5) # Right hand
                        all_notes_lh_alternating += add_note(note=note + 12*(octave-1), start_beat=2*(c+7*octave), length_in_beats=0.5) # Left hand
                    note += i
                all_notes += add_note(note=key + 12*num_octaves_scale, start_beat=7*num_octaves_scale, length_in_beats=0.5) # Right hand
                all_notes += add_note(note=key + 12*(num_octaves_scale-1), start_beat=7*num_octaves_scale, length_in_beats=0.5) # Left hand
                all_notes_lh_alternating += add_note(note=key + 12*num_octaves_scale, start_beat=2*(7*num_octaves_scale) + 1, length_in_beats=0.5) # Right hand
                all_notes_lh_alternating += add_note(note=key + 12*(num_octaves_scale-1), start_beat=2*(7*num_octaves_scale), length_in_beats=0.5) # Left hand
                makefile(all_notes, savedir, '{}_{}.mid'.format(scale, key))
                makefile(all_notes_lh_alternating, savedir, '{}_{}_lh_alternating.mid'.format(scale, key))

        # Write descending scales for all keys
        for scale in scales_dec:
            for key in range(96, 84, -1): # Iterate over all keys
                all_notes = []
                all_notes_lh_alternating = []
                note = key
                for c, i in enumerate(scales_dec[scale]): # Iterate over all notes within the scale
                    for octave in range(num_octaves_scale):
                        all_notes += add_note(note=note - 12*octave, start_beat=c+7*octave, length_in_beats=0.5) # Right hand
                        all_notes += add_note(note=note - 12*(octave+1), start_beat=c+7*octave, length_in_beats=0.5) # Left hand
                        all_notes_lh_alternating += add_note(note=note - 12*octave, start_beat=2*(c+7*octave) + 1, length_in_beats=0.5) # Right hand
                        all_notes_lh_alternating += add_note(note=note - 12*(octave-1), start_beat=2*(c+7*octave), length_in_beats=0.5) # Left hand
                    note += i
                all_notes += add_note(note=key - 12*num_octaves_scale, start_beat=7*num_octaves_scale, length_in_beats=0.5) # Right hand
                all_notes += add_note(note=key - 12*(num_octaves_scale+1), start_beat=7*num_octaves_scale, length_in_beats=0.5) # Left hand
                all_notes_lh_alternating += add_note(note=key - 12*num_octaves_scale, start_beat=2*(7*num_octaves_scale) + 1, length_in_beats=0.5) # Right hand
                all_notes_lh_alternating += add_note(note=key - 12*(num_octaves_scale-1), start_beat=2*(7*num_octaves_scale), length_in_beats=0.5) # Left hand
                makefile(all_notes, savedir, '{}_{}.mid'.format(scale, key))
                makefile(all_notes_lh_alternating, savedir, '{}_{}_lh_alternating.mid'.format(scale, key))

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
            for key in range(36, 48): # Iterate over all keys
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
            for key in range(96, 84, -1): # Iterate over all keys
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
            for key in range(36, 48): # Iterate over all keys
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
            for key in range(96, 84, -1): # Iterate over all keys
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