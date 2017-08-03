class MusicNote(object):
    Notes = dict()

    def __init__(self, name, midi_value):
        self.name = name
        self.midi_value = midi_value
        self.frequecy =  (2**((midi_value-69)/12.))*440

    @staticmethod
    def populate():
        if MusicNote.Notes:
            return
        note_names = "C C# D D# E F F# G G# A A# B".split(" ")
        for octave in xrange(11):
            for note_i in xrange(len(note_names)):
                note_name = note_names[note_i]
                if octave == 10 and  note_name == "G#":
                    break
                note = MusicNote(
                        name="{0}{1}".format(note_name, octave),
                        midi_value = octave*12+note_i)
                MusicNote.Notes[note.name] = note

MusicNote.populate()
