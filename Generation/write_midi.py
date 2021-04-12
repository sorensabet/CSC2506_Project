import pretty_midi
import numpy as np
import pandas as pd 

from mido import Message, MidiFile, MidiTrack, MetaMessage

pd.options.mode.chained_assignment = None


def set_piano_roll_to_instrument(piano_roll, instrument, velocity=64, tempo=120.0, beat_resolution=4):
    # Calculate time per pixel
    tpp = 60.0 / tempo / float(beat_resolution)      # 0.125 seconds per pixel 
    threshold = 60.0 / tempo / 4                     # 0.125 (unit unclear)
    phrase_end_time = (60.0 / tempo) * piano_roll.shape[1] / beat_resolution
    
    # Create piano_roll_search that captures note onsets and offsets
    orig_piano_roll = piano_roll
    piano_roll = piano_roll.reshape((piano_roll.shape[0] * piano_roll.shape[1], piano_roll.shape[2]))   
    piano_roll_diff = np.concatenate((np.zeros((1, 128), dtype=int), piano_roll, np.zeros((1, 128), dtype=int)))
    piano_roll_search = np.diff(piano_roll_diff.astype(int), axis=0)
    # Iterate through all possible(128) pitches

    for note_num in range(128):
        #print('Note Num: %d' % note_num)
        # Search for notes
        start_idx = (piano_roll_search[:, note_num] > 0).nonzero()
        start_time = list(tpp * (start_idx[0].astype(float)))
        # print('start_time:', start_time)
        # print(len(start_time))
        end_idx = (piano_roll_search[:, note_num] < 0).nonzero()
        end_time = list(tpp * (end_idx[0].astype(float)))
        # print('end_time:', end_time)
        # print(len(end_time))
        duration = [pair[1] - pair[0] for pair in zip(start_time, end_time)]
        # print('duration each note:', duration)
        # print(len(duration))

        temp_start_time = [i for i in start_time]
        temp_end_time = [i for i in end_time]

        for i in range(len(start_time)):
            #print(start_time)
            if start_time[i] in temp_start_time and i != len(start_time) - 1:
                # print('i and start_time:', i, start_time[i])
                t = []
                current_idx = temp_start_time.index(start_time[i])
                for j in range(current_idx + 1, len(temp_start_time)):
                    # print(j, temp_start_time[j])
                    if temp_start_time[j] < start_time[i] + threshold and temp_end_time[j] <= start_time[i] + threshold:
                        # print('popped start time:', temp_start_time[j])
                        t.append(j)
                        # print('popped temp_start_time:', t)
                for _ in t:
                    temp_start_time.pop(t[0])
                    temp_end_time.pop(t[0])
                # print('popped temp_start_time:', temp_start_time)

        start_time = temp_start_time
        # print('After checking, start_time:', start_time)
        # print(len(start_time))
        end_time = temp_end_time
        # print('After checking, end_time:', end_time)
        # print(len(end_time))
        duration = [pair[1] - pair[0] for pair in zip(start_time, end_time)]
        # print('After checking, duration each note:', duration)
        # print(len(duration))

        if len(end_time) < len(start_time):
            d = len(start_time) - len(end_time)
            start_time = start_time[:-d]
        # Iterate through all the searched notes
        for idx in range(len(start_time)):
            if duration[idx] >= threshold:
                # Create an Note object with corresponding note number, start time and end time
                note = pretty_midi.Note(velocity=velocity, pitch=note_num, start=start_time[idx], end=end_time[idx])
                # Add the note to the Instrument object
                instrument.notes.append(note)
            else:
                if start_time[idx] + threshold <= phrase_end_time:
                    # Create an Note object with corresponding note number, start time and end time
                    note = pretty_midi.Note(velocity=velocity, pitch=note_num, start=start_time[idx],
                                            end=start_time[idx] + threshold)
                else:
                    # Create an Note object with corresponding note number, start time and end time
                    note = pretty_midi.Note(velocity=velocity, pitch=note_num, start=start_time[idx],
                                            end=phrase_end_time)
                # Add the note to the Instrument object
                instrument.notes.append(note)
    # Sort the notes by their start time
    instrument.notes.sort(key=lambda note: note.start)
    # print(max([i.end for i in instrument.notes]))
    # print('tpp, threshold, phrases_end_time:', tpp, threshold, phrase_end_time)
    
def generate_mido(notes): 
    
    note_dict = []
    for n in notes: 
        note_dict.append({'note': n.pitch, 'start(s)': n.start, 'end(s)': n.end, 'velocity': 64})
    df = pd.DataFrame.from_records(note_dict)
    
    dfs = df[['note', 'start(s)']]
    dfs['type'] = 'note_on'
    dfs['start_beat'] = dfs['start(s)']*2
    
    dfe = df[['note', 'end(s)']]
    dfe['type'] = 'note_off'
    dfe['start_beat'] = dfe['end(s)']*2
    
    df2 = pd.concat([dfs[['note', 'type', 'start_beat']], dfe[['note', 'type', 'start_beat']]])
    df2.sort_values(by=['start_beat'], inplace=True)
    df2['ctime'] = df2['start_beat']*480                                         # Use 480 ticks per beat 
    df2['time'] = df2['ctime'] - df2['ctime'].shift(1)                            # MIDI commands are sequential, we need to go from cumulative time to time between events
    df2 = df2.fillna(0)
    
    ### USING MIDO TO GENERATE MIDI FILES #### 
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
       
    midiTrack += [Message(x[2],  note=int(x[1]), time=int(x[5]), velocity=64, channel=0) for x in df2.itertuples()]
    
    # End of Track MIDI Message
    midiTrack.append(MetaMessage('end_of_track', time=0))
    
    # Append Track to MIDI File
    mid.tracks.append(midiTrack)
    
    #mid.save(savedir + '/' + filename + '_' + str(s) + '.mid')
    # print('Generated MIDO file!')
    # print(savedir + '/' + filename + '_' + str(s) + '.mid')
    return mid 


def write_piano_roll_to_midi(piano_roll, filename, program_num=0, is_drum=False, velocity=64,
                             tempo=120.0, beat_resolution=16):
    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    # Create an Instrument object
    instrument = pretty_midi.Instrument(program=program_num, is_drum=is_drum)
    # Set the piano roll to the Instrument object

    set_piano_roll_to_instrument(piano_roll, instrument, velocity, tempo, beat_resolution)
    
    mido = generate_mido(instrument.notes)
    
    mido.save(filename)    

def write_piano_rolls_to_midi(piano_rolls, program_nums=None, is_drum=None, filename='test.mid', velocity=100,
                              tempo=120.0, beat_resolution=24):
    
    print('WARNING! THIS FUNCTION HAS BEEN MODIFIED TO WITH ADDITIONAL FUNCTIONALITY TO SAVE INDIVIDUAL TRACKS')
    print('AS STANDALONE MIDI FILES. IT IS STRONGLY RECOMMENDED THAT YOU USE THE SINGLE TRACK VERSION!')
    
    if len(piano_rolls) != len(program_nums) or len(piano_rolls) != len(is_drum):
        print("Error: piano_rolls and program_nums have different sizes...")
        return False
    if not program_nums:
        program_nums = [0, 0, 0]
    if not is_drum:
        is_drum = [False, False, False]
    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    # Iterate through all the input instruments
    for idx in range(len(piano_rolls)):
        # Create an Instrument object
        instrument = pretty_midi.Instrument(program=program_nums[idx], is_drum=is_drum[idx])
        # Set the piano roll to the Instrument object
        set_piano_roll_to_instrument(piano_rolls[idx], instrument, velocity, tempo, beat_resolution)
        # Add the instrument to the PrettyMIDI object
        midi.instruments.append(instrument)
        
        temp_filename = filename.split('.')[0]
        mido = generate_mido(instrument.notes)
        mido.save(temp_filename + '_track' + str(idx) + '.mid')
    # Write out the MIDI data
    midi.write(filename)