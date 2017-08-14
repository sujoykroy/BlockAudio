import numpy
import time
from ..commons import MidiMessage, AudioMessage

class BlockTime(object):
    def __init__(self, xvalue, unit):
        self.value = pos_value
        self.unit = unit

class AudioBlock(object):
    FramesPerBuffer = 1024
    SampleRate = 44100.
    ChannelCount = 2

    LOOP_NONE = 0
    LOOP_INFINITE = 1
    LOOP_STRETCH = 2

    TIME_UNIT_SAMPLE = 0
    TIME_UNIT_SECONDS = 1
    TIME_UNIT_BEAT = 2
    TIME_UNIT_DIV = 3

    IdSeed = 0
    NameSeed = 0
    _APP_EPOCH_TIME = time.mktime(time.strptime("1 Jan 2017", "%d %b %Y"))

    @staticmethod
    def new_name():
        AudioBlock.NameSeed += 1
        elapsed_time = round(time.time()-AudioBlock._APP_EPOCH_TIME, 3)
        return "{0}_{1}".format(elapsed_time, AudioBlock.NameSeed).replace(".", "")

    @classmethod
    def get_time_unit_model(cls):
        return [
            ["Seconds", cls.TIME_UNIT_SECONDS],
            ["Beat", cls.TIME_UNIT_BEAT],
            ["Div", cls.TIME_UNIT_DIV],
            ["Sample", cls.TIME_UNIT_SAMPLE]
        ]

    def __init__(self):
        self.paused = False
        self.loop = self.LOOP_STRETCH
        self.duration_unit = self.TIME_UNIT_SAMPLE
        self.duration_value = 0
        self.duration = 0
        self.inclusive_duration = 0
        self.auto_fit_duration = True
        self.current_pos = 0
        self.music_note = "C5"
        self.midi_channel = None
        self.midi_velocity = 64
        self.play_pos = 0
        self.instru = None

        self.id_num = AudioBlock.IdSeed
        AudioBlock.IdSeed += 1
        self.name = self.new_name()

    def build(self, beat):
        self._build_duration(beat)

    def __eq__(self, other):
        return isinstance(other, AudioBlock) and other.id_num == self.id_num

    def set_current_pos(self, current_pos):
        self.current_pos = current_pos

    def set_music_note(self, note):
        self.music_note = note

    def set_midi_channel(self, channel):
        self.midi_channel = channel

    def set_instru(self, instru):
        self.instru = instru

    def set_note(self, note):
        self.music_note = note
        if self.instru:
            self.instru.refill_block(self)

    def new_midi_note_on_message(self, delay):
        return MidiMessage.note_on(
                        delay=delay,
                        note=self.music_note,
                        velocity=self.midi_velocity,
                        channel=self.midi_channel)

    def new_midi_note_off_message(self, delay):
        return MidiMessage.note_off(
                        delay=delay,
                        note=self.music_note,
                        channel=self.midi_channel)

    def set_duration(self, duration, beat):
        if duration<=0:
            return

        self.auto_fit_duration = False
        self.duration = duration
        self._build_duration_value(beat)

    def _build_duration_value(self, beat):
        if self.duration_unit == self.TIME_UNIT_BEAT:
            self.duration_value = self.duration*1./beat.get_beat_sample(1)
        elif self.duration_unit == self.TIME_UNIT_DIV:
            self.duration_value = self.duration*1./beat.get_div_sample(1)
        elif self.duration_unit == self.TIME_UNIT_SECONDS:
            print self.duration, self.SampleRate
            self.duration_value = self.duration*1./self.SampleRate
        else:
            self.duration_value = self.duration

    def set_duration_value(self, duration_value, beat):
        if duration_value <= 0:
            return
        self.auto_fit_duration = False
        self.duration_value = duration_value
        self._build_duration(beat)

    def _build_duration(self, beat):
        if self.duration_unit == self.TIME_UNIT_BEAT:
            duration = beat.get_beat_sample(self.duration_value)
        elif self.duration_unit == self.TIME_UNIT_DIV:
            duration = beat.get_div_sample(self.duration_value)
        elif self.duration_unit == self.TIME_UNIT_SECONDS:
            duration = self.duration_value*self.SampleRate
        else:
            duration = self.duration_value
        self.duration = int(round(duration))

    def set_duration_unit(self, duration_unit, beat):
        self.duration_unit = duration_unit
        self._build_duration_value(beat)

    def get_id(self):
        return self.id_num

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def calculate_duration(self):
        if self.auto_fit_duration:
            self.duration = self.inclusive_duration

    def get_time_duration(self):
        return self.duration/AudioBlock.SampleRate

    def get_samples(self, frame_count, start_from=None, use_loop=True, loop=None):
        return AudioMessage(self.get_blank_data(frame_count))

    def get_description(self):
        if self.instru:
            desc = self.instru.get_description()
            return desc
        return self.name

    @staticmethod
    def get_blank_data(sample_count):
        return numpy.zeros((sample_count, AudioBlock.ChannelCount), dtype=numpy.float32)


