from audio_instru import AudioInstru
from ..commons import MusicNote, SamplesProcessor
from audio_samples_block import AudioSamplesBlock

class AudioSamplesInstru(AudioInstru):
    def __init__(self, samples, base_note="C5"):
        AudioInstru.__init__(self)
        self.samples = samples
        self.base_note = MusicNote.get_note(base_note)
        self.notes_samples = dict()

    def get_samples_for(self, note):
        if isinstance(note, str):
            note = MusicNote.get_note(note)
        if note.name not in self.notes_samples:
           factor = note.frequency/self.base_note.frequency
           samples = SamplesProcessor.speed_up(self.samples, factor)
           self.notes_samples[note.name] = samples
        else:
            samples = self.notes_samples[note.name]
        return samples

    def create_note_block(self, note="C5"):
        note = MusicNote.get_note(note)
        note_block = AudioSamplesBlock(self.get_samples_for(note))
        note_block.set_instru(self)
        note_block.set_music_note(note.name)
        return note_block

    def refill_block(self, block):
        block.samples = self.get_samples_for(block.music_note)
