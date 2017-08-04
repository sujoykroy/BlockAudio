from audio_instru import AudioInstru
from ..commons import MusicNote, SamplesProcessor
from audio_samples_block import AudioSamplesBlock

class AudioSamplesInstru(AudioInstru):
    def __init__(self, samples, base_note="C5"):
        AudioInstru.__init__(self)
        self.samples = samples
        self.base_note = MusicNote.get_note(base_note)

    def create_note_block(self, note):
        if note != self.base_note.name or True:
           note = MusicNote.get_note(note)
           factor = note.frequency/self.base_note.frequency
           samples = SamplesProcessor.pitch_shift(self.samples, factor)
        else:
            samples = self.samples
            note = self.base_note
        note_block = AudioSamplesBlock(samples)
        note_block.set_music_note(note.name)
        return note_block

