from audio_instru import AudioInstru
from ..commons import MusicNote, SamplesProcessor
from audio_samples_block import AudioSamplesBlock
from audio_block import AudioBlock
import imp
import numpy

class AudioFormulaInstru(AudioInstru):
    def __init__(self, formulator, base_note="C5"):
        AudioInstru.__init__(self)
        self.base_note = MusicNote.get_note(base_note)
        self.params = dict()
        self.base_duration = 1.
        self.formulator = None
        if isinstance(formulator, str):
            self.load_formulator(filepath)
        else:
            self.formulator = formulator
        self.note_samples = dict()

    def load_formulator(self, filepath):
        if not os.path.isfile(filepath):
            return
        self.formula_module = imp.load_source("formula_module", filepath)
        if hasattr(self.formula_module, "Formulator"):
            self.formulator = self.formula_module.Formulator()
            self.set_params(self.params)

    def set_formulator(self, formulator):
        self.formulator = formulator

    def set_base_duration(self, duration):
        self.base_duration = duration

    def create_note_block(self, note):
        if self.formulator:
            note = MusicNote.get_note(note)
            if note.name not in self.note_samples:
                samples = self.formulator.get_note_samples(
                                note, self.base_note, self.base_duration,
                                AudioBlock.ChannelCount, AudioBlock.SampleRate)
                if samples is not None and len(samples.shape)==1:
                    samples = numpy.repeat(samples, AudioBlock.ChannelCount)
                    samples.shape = (-1, AudioBlock.ChannelCount)
                self.note_samples[note.name] = samples
            else:
                samples = self.note_samples.get(note.name)
        else:
            samples = numpy.zeros((1, AudioBlock.ChannelCount), dtype=numpy.float32)
        note_block = AudioSamplesBlock(samples)
        note_block.set_music_note(note.name)

        #note_block.save_to_file("/home/sujoy/Temporary/sound_" + note.name + ".wav")
        return note_block

