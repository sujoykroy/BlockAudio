from audio_instru import AudioInstru
from ..commons import MusicNote, SamplesProcessor
from audio_samples_block import AudioSamplesBlock

class AudioSamplesInstru(AudioInstru):
    def __init__(self, samples, base_note="C5"):
        AudioInstru.__init__(self)
        self.samples = samples
        self.base_note = MusicNote.get_note(base_note)
        self.notes_samples = dict()

    def create_note_block(self, note):
        if note not in self.notes_samples:
           note = MusicNote.get_note(note)
           factor = note.frequency/self.base_note.frequency
           samples = SamplesProcessor.speed_up(self.samples, factor)
           self.notes_samples[note.name] = samples
        else:
            samples = self.notes_samples[note]

        note_block = AudioSamplesBlock(samples)
        note_block.set_music_note(note.name)
        return note_block

