from music_note import MusicNote
import mido

class MidiMessage(object):
    def __init__(self, delay, mido_message):
        self.delay = delay
        self.mido_message = mido_message

    def increase_delay(self, incre):
        self.delay += incre

    @classmethod
    def note_on(cls, delay, note, channel, velocity=64):
        note = MusicNote.Notes[note]
        return cls(delay, mido.Message(
            'note_on', note=note.midi_value, channel=channel, velocity=velocity))

    @classmethod
    def note_off(cls, delay, note, channel):
        note = MusicNote.Notes[note]
        return cls(delay, mido.Message(
            'note_off', note=note.midi_value, channel=channel, velocity=0))

