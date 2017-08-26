from audio_instru import AudioInstru
from ..commons import MusicNote, SamplesProcessor
from audio_samples_block import AudioSamplesBlock

class AudioSamplesInstru(AudioInstru):
    def __init__(self, samples, base_note="C5"):
        AudioInstru.__init__(self)
        self.samples = samples
        self.base_note = MusicNote.get_note(base_note)
        self.notes_samples = dict()

    def get_xml_element(self):
        elm = super(AudioSamplesInstru, self).get_xml_element()
        elm.attrib["base_note"] = self.base_note.name
        return elm

    def load_from_xml(self, elm):
        super(AudioSamplesInstru, self).load_from_xml(elm)
        self.base_note = MusicNote.get_note(elm.attrib.get("base_note"))

    def get_samples_for(self, note):
        if isinstance(note, str):
            note = MusicNote.get_note(note)
        if note.name not in self.notes_samples:
            factor = note.frequency/self.base_note.frequency
            if factor == 1:
                samples = self.samples.copy()
            else:
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
        self.add_block(note_block)
        return note_block

    def readjust_blocks(self):
        for note_name in self.notes_samples:
            del self.notes_samples[note_name]
            self.notes_samples[note_name] = self.get_samples_for(note_name)
        for block in self.blocks:
            if isinstance(block, AudioSamplesBlock):
                block.set_samples(self.get_samples_for(block.music_note))
            else:
                block.readjust()

    def refill_block(self, block):
        block.samples = self.get_samples_for(block.music_note)

