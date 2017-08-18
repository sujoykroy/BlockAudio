from audio_instru import AudioInstru
from ..commons import MusicNote, SamplesProcessor
from audio_samples_block import AudioSamplesBlock
from audio_block import AudioBlock, AudioBlockTime
import imp
import numpy
import os

class AudioFormulaInstru(AudioInstru):
    def __init__(self, formulator, base_note="C5"):
        AudioInstru.__init__(self)
        self.base_note = MusicNote.get_note(base_note)
        self.duration_time = AudioBlockTime(AudioBlock.SampleRate)

        self.formulator_path = None

        if formulator is None:
            self.formulator = None
            self.customized = True
        else:
            self.customized = False
            self.formulator = formulator(self)

        self.notes_samples = dict()
        self.autogen_other_notes = True

    def is_customized(self):
        return self.customized

    def load_formulator(self, filepath):
        self.formulator_path = filepath
        if not os.path.isfile(filepath):
            return
        self.formula_module = imp.load_source("formula_module", filepath)
        if hasattr(self.formula_module, "Formulator"):
            self.formulator = self.formula_module.Formulator(self)
        self.readjust_note_blocks()

    def get_param_list(self):
        if self.formulator and hasattr(self.formulator, "get_param_list"):
            return self.formulator.get_param_list()
        return []

    def set_param(self, param_name, param_data):
        if self.formulator and hasattr(self.formulator, "set_param"):
            self.formulator.set_param(param_name, param_data)

    def set_duration_value(self, value, beat):
        self.duration_time.set_value(value, beat)
        self.readjust_note_blocks()

    def set_duration_unit(self, unit, beat):
        self.duration_time.set_unit(unit, beat)

    def set_duration(self, duration, beat):
        self.duration_time.set_sample_count(duration, beat)
        self.readjust_note_blocks()

    def get_sample_rate(self):
        return AudioBlock.SampleRate

    def get_samples_for(self, note):
        if not self.formulator:
            return numpy.zeros((1, AudioBlock.ChannelCount), dtype=numpy.float32)

        if isinstance(note, str):
            note = MusicNote.get_note(note)
        if note.name not in self.notes_samples:
            if note.name == self.base_note.name or not self.autogen_other_notes:
                samples = self.formulator.get_note_samples(note)
                if samples is not None and len(samples.shape)==1:
                    samples = numpy.repeat(samples, AudioBlock.ChannelCount)
                    samples.shape = (-1, AudioBlock.ChannelCount)
            else:
                factor = note.frequency/self.base_note.frequency
                samples = SamplesProcessor.speed_up(
                    self.get_samples_for(self.base_note), factor)
            self.notes_samples[note.name] = samples
        else:
            samples = self.notes_samples.get(note.name)
        return samples

    def create_note_block(self, note="C5"):
        note = MusicNote.get_note(note)
        note_block = AudioSamplesBlock(self.get_samples_for(note))
        note_block.set_instru(self)
        note_block.set_music_note(note.name)
        return note_block

    def readjust_note_blocks(self):
        for note_name in self.notes_samples:
            del self.notes_samples[note_name]
            self.notes_samples[note_name] = self.get_samples_for(note_name)
        for block in self.note_blocks:
            block.set_samples(self.notes_samples[block.music_note])
            print block.get_duration()
