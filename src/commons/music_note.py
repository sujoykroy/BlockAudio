class MusicNote(object):
    ByNames = dict()
    ByMidis = dict()

    def __init__(self, name, midi_value):
        self.name = name
        self.midi_value = midi_value
        self.frequency =  (2**((midi_value-69)/12.))*440

    @staticmethod
    def get_note(note):
        return MusicNote.ByNames.get(note)

    def get_next_note(self, incre=1):
        next_midi_value = self.midi_value + incre
        if next_midi_value in self.ByMidis:
            return self.ByMidis.get(next_midi_value)
        return None

    @staticmethod
    def populate():
        if MusicNote.ByNames:
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
                MusicNote.ByNames[note.name] = note
                MusicNote.ByMidis[note.midi_value] = note

MusicNote.populate()
