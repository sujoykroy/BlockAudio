from audio_instru import AudioInstru
from ..commons import MusicNote, SamplesProcessor
from audio_samples_block import AudioSamplesBlock
from audio_block import AudioBlock, AudioBlockTime
import imp
import numpy
import os
from xml.etree.ElementTree import Element as XmlElement

class AudioFormulaInstru(AudioInstru):
    PARAM_TAG_NAME = "param"

    def __init__(self, formulator=None, base_note="C5", filepath=None):
        AudioInstru.__init__(self)
        self.base_note = MusicNote.get_note(base_note)
        self.duration_time = AudioBlockTime(AudioBlock.SampleRate)

        self.formulator_path = None
        self.notes_samples = dict()
        self.autogen_other_notes = True

        if formulator is None:
            self.formulator = None
            self.customized = True
            if filepath:
                self.load_formulator(filepath)
        else:
            self.customized = False
            self.formulator = formulator(self)

    def get_xml_element(self):
        elm = super(AudioFormulaInstru, self).get_xml_element()
        if self.formulator_path:
            elm.attrib["formulator_path"] = self.formulator_path
            for param_data in self.get_param_list():
                param_name = param_data[0]
                param_value = "{0}".format(self.get_param(param_name))

                param_elm = XmlElement(self.PARAM_TAG_NAME)
                param_elm.attrib["name"] = param_name
                param_elm.attrib["value"] = param_value
                elm.append(param_elm)
        else:
            elm.attrib["formulator"] = self.formulator.DISPLAY_NAME
        elm.attrib["autogen"] = "{0}".format(int(self.autogen_other_notes))
        return elm

    def is_customized(self):
        return self.customized

    def load_formulator(self, filepath):
        self.formulator_path = filepath
        if not os.path.isfile(filepath):
            return
        self.formula_module = imp.load_source("formula_module", filepath)
        if hasattr(self.formula_module, "Formulator"):
            self.formulator = self.formula_module.Formulator(self)
        self.readjust_blocks()

    def get_param_list(self):
        if self.formulator:
            if hasattr(self.formulator, "param_list"):
                return self.formulator.param_list
        return dict()

    def get_param(self, param_name):
        if not self.formulator:
            return None
        if hasattr(self.formulator, param_name):
            return getattr(self.formulator, param_name)
        return None

    def set_param(self, param_name, param_value):
        if not self.formulator:
            return

        param_list = self.get_param_list()
        for param_data in self.get_param_list():
            if param_data[0] == param_name:
                param_type = param_data[1]
                if param_type == float:
                    param_value = float(param_value)
                if hasattr(self.formulator, param_name):
                    setattr(self.formulator, param_name, param_value)
                self.readjust_blocks()
                return

    def set_duration_value(self, value, beat):
        self.duration_time.set_value(value, beat)
        self.readjust_blocks()

    def set_duration_unit(self, unit, beat):
        self.duration_time.set_unit(unit, beat)

    def set_duration(self, duration, beat):
        self.duration_time.set_sample_count(duration, beat)
        self.readjust_blocks()

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
        self.add_block(note_block)
        return note_block

    def readjust_blocks(self):
        if not self.notes_samples:
            return
        for note_name in self.notes_samples:
            del self.notes_samples[note_name]
            self.notes_samples[note_name] = self.get_samples_for(note_name)
        for block in self.blocks:
            block.set_samples(self.notes_samples[block.music_note])

    def refill_block(self, block):
        block.set_samples(self.get_samples_for(block.music_note))
