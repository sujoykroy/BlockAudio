import numpy
import time
import threading
from ..commons import MidiMessage, AudioMessage

class AudioBlockTime(object):
    TIME_UNIT_SAMPLE = 0
    TIME_UNIT_SECONDS = 1
    TIME_UNIT_BEAT = 2
    TIME_UNIT_DIV = 3

    @classmethod
    def get_model(cls):
        return [
            ["Seconds", cls.TIME_UNIT_SECONDS],
            ["Beat", cls.TIME_UNIT_BEAT],
            ["Div", cls.TIME_UNIT_DIV],
            ["Sample", cls.TIME_UNIT_SAMPLE]
        ]

    def __init__(self, value=0, unit=None):
        self.value = value
        if unit is None:
            unit = self.TIME_UNIT_SAMPLE
        self.unit = unit
        if unit == self.TIME_UNIT_SAMPLE:
            self.sample_count = value
        else:
            self.sample_count = None

    def build(self, beat):
        self._build_sample_count(beat)

    def set_value(self, value, beat):
        self.value = value
        self._build_sample_count(beat)

    def set_sample_count(self, sample_count, beat):
        self.sample_count = sample_count
        self._build_value(beat)

    def set_unit(self, unit, beat):
        self.unit = unit
        self._build_value(beat)

    def _build_value(self, beat):
        if self.unit == self.TIME_UNIT_BEAT:
            self.value = self.sample_count*1./beat.get_beat_sample(1)
        elif self.unit == self.TIME_UNIT_DIV:
            self.value = self.sample_count*1./beat.get_div_sample(1)
        elif self.unit == self.TIME_UNIT_SECONDS:
            self.value = self.sample_count*1./beat.sample_rate
        else:
            self.value = self.sample_count

    def _build_sample_count(self, beat):
        if self.unit == self.TIME_UNIT_BEAT:
            sample_count = beat.get_beat_sample(self.value)
        elif self.unit == self.TIME_UNIT_DIV:
            sample_count = beat.get_div_sample(self.value)
        elif self.unit == self.TIME_UNIT_SECONDS:
            sample_count = self.value*beat.sample_rate
        else:
            sample_count = self.value
        self.sample_count = int(round(sample_count))

class AudioBlock(object):
    FramesPerBuffer = 1024
    SampleRate = 44100.
    ChannelCount = 2

    LOOP_NONE = 0
    LOOP_INFINITE = 1
    LOOP_STRETCH = 2
    LOOP_NEVER_EVER = 3

    IdSeed = 0
    NameSeed = 0
    _APP_EPOCH_TIME = time.mktime(time.strptime("1 Jan 2017", "%d %b %Y"))

    @staticmethod
    def new_name():
        AudioBlock.NameSeed += 1
        elapsed_time = round(time.time()-AudioBlock._APP_EPOCH_TIME, 3)
        return "{0}_{1}".format(elapsed_time, AudioBlock.NameSeed).replace(".", "")

    def __init__(self):
        self.paused = False
        self.loop = self.LOOP_STRETCH
        self.duration_time = AudioBlockTime()
        self.duration = 0
        self.inclusive_duration = 0
        self.auto_fit_duration = True
        self.current_pos = 0
        self.music_note = "C5"
        self.midi_channel = None
        self.midi_velocity = 64
        self.play_pos = 0
        self.instru = None
        self.lock = threading.RLock()

        self.id_num = AudioBlock.IdSeed
        AudioBlock.IdSeed += 1
        self.name = self.new_name()

    def build(self, beat):
        self.duration_time.build(beat)

    def __eq__(self, other):
        return isinstance(other, AudioBlock) and other.id_num == self.id_num

    def set_current_pos(self, current_pos):
        self.current_pos = current_pos

    def set_play_pos(self, play_pos):
        self.play_pos = play_pos

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

    def set_no_loop(self):
        self.loop = self.LOOP_NEVER_EVER

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

    def set_sample_count(self, sample_count):
        self.duration_time.set_sample_count(sample_count, beat=None)
        self.duration = self.duration_time.sample_count

    def set_duration(self, duration, beat):
        if duration<=0:
            return

        self.auto_fit_duration = False
        self.duration_time.set_sample_count(duration, beat)
        self.duration = self.duration_time.sample_count

    def set_duration_value(self, duration_value, beat):
        if duration_value <= 0:
            return
        self.auto_fit_duration = False
        self.duration_time.set_value(duration_value, beat)
        self.duration = self.duration_time.sample_count

    def set_duration_unit(self, duration_unit, beat):
        self.duration_time.set_unit(duration_unit, beat)

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

    def is_reading_finished(self):
        return self.current_pos >= self.duration

    def is_playing_finished(self):
        return self.play_pos >= self.duration

    def rewind(self):
        self.lock.acquire()
        self.current_pos = 0
        self.play_pos = 0
        self.lock.release()

    @staticmethod
    def get_blank_data(sample_count):
        return numpy.zeros((sample_count, AudioBlock.ChannelCount), dtype=numpy.float32)


