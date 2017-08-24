import numpy
import time
import threading
from ..commons import MidiMessage, AudioMessage
from xml.etree.ElementTree import Element as XmlElement

class AudioBlockTime(object):
    TIME_UNIT_SAMPLE = 0
    TIME_UNIT_SECONDS = 1
    TIME_UNIT_BEAT = 2
    TIME_UNIT_DIV = 3


    BEAT_UNIT_NAMES = ("beat",)
    DIV_UNIT_NAMES = ("div",)
    SECONDS_UNIT_NAMES = ("seconds", "sec")
    SAMPLE_UNIT_NAMES = ("sample", )

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
            self.sample_count = int(value)
        else:
            self.sample_count = None

    def copy(self):
        newob = AudioBlockTime(self.value, self.unit)
        newob.sample_count = self.sample_count
        return newob

    def recompute(self, beat):
        self._build_sample_count(beat)

    def set_value(self, value, beat):
        self.value = value
        self._build_sample_count(beat)

    def get_seconds(self, beat):
        return self.sample_count*1./beat.sample_rate

    def set_sample_count(self, sample_count, beat):
        self.sample_count = sample_count
        self._build_value(beat)

    def set_unit(self, unit, beat):
        if unit in self.BEAT_UNIT_NAMES:
            unit = self.TIME_UNIT_BEAT
        elif unit in self.DIV_UNIT_NAMES:
            unit = self.TIME_UNIT_DIV
        elif unit in self.SECONDS_UNIT_NAMES:
            unit = self.TIME_UNIT_SECONDS
        elif unit in self.SAMPLE_UNIT_NAMES:
            unit = self.TIME_UNIT_SAMPLE
        self.unit = unit
        self._build_value(beat)

    def _build_value(self, beat):
        if self.unit == self.TIME_UNIT_BEAT or \
                        self.unit in self.BEAT_UNIT_NAMES:
            self.value = self.sample_count*1./beat.get_beat_sample(1)
        elif self.unit == self.TIME_UNIT_DIV or \
                        self.unit in self.DIV_UNIT_NAMES:
            self.value = self.sample_count*1./beat.get_div_sample(1)
        elif self.unit == self.TIME_UNIT_SECONDS or \
                        self.unit in self.SECONDS_UNIT_NAMES:
            self.value = self.sample_count*1./beat.sample_rate
        else:
            self.value = self.sample_count

    def _build_sample_count(self, beat):
        if self.unit == self.TIME_UNIT_BEAT or \
                        self.unit in self.BEAT_UNIT_NAMES:
            sample_count = beat.get_beat_sample(self.value)
        elif self.unit == self.TIME_UNIT_DIV or \
                        self.unit in self.DIV_UNIT_NAMES:
            sample_count = beat.get_div_sample(self.value)
        elif self.unit == self.TIME_UNIT_SECONDS or \
                        self.unit in self.SECONDS_UNIT_NAMES:
            sample_count = self.value*beat.sample_rate
        else:
            sample_count = self.value
        self.sample_count = int(round(sample_count))

    def to_text(self):
        return "{0}:{1}:{2}".format(self.value, self.unit, self.sample_count)

    @classmethod
    def from_text(cls, text):
        arr = text.split(":")
        newob =cls(float(arr[0]), int(arr[1]))
        newob.sample_count = int(arr[2])
        return newob

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

    TAG_NAME = "adblck"
    TYPE_NAME = ""

    @staticmethod
    def new_name():
        AudioBlock.NameSeed += 1
        elapsed_time = round(time.time()-AudioBlock._APP_EPOCH_TIME, 3)
        return "{0}_{1}".format(elapsed_time, AudioBlock.NameSeed).replace(".", "")

    def __init__(self):
        self.paused = False
        self.loop = self.LOOP_STRETCH

        self.start_time = AudioBlockTime()
        self.duration_time = AudioBlockTime()
        self.y = 0

        self.duration = 0
        self.inclusive_duration = 0
        self.auto_fit_duration = True

        self.current_pos = 0
        self.play_pos = 0

        self.music_note = "C5"
        self.midi_channel = None
        self.midi_velocity = 64

        self.instru = None
        self.owner = None
        self.lock = threading.RLock()

        self.id_num = AudioBlock.IdSeed
        AudioBlock.IdSeed += 1
        self.name = self.new_name()

    def copy_values_into(self, newob):
        newob.loop = self.loop
        newob.start_time = self.start_time.copy()
        newob.duration_time = self.duration_time.copy()
        newob.y = self.y
        newob.duration = self.duration
        newob.inclusive_duration = self.inclusive_duration
        newob.auto_fit_duration = self.auto_fit_duration
        newob.instru = self.instru
        return newob

    def get_xml_element(self):
        elm = XmlElement(self.TAG_NAME)
        elm.attrib["y"] = "{0}".format(self.y)
        elm.attrib["type"] = self.TYPE_NAME
        elm.attrib["name"] = "{0}".format(self.get_name())
        elm.attrib["loop"] = "{0}".format(self.loop)
        elm.attrib["duration"] = self.duration_time.to_text()
        elm.attrib["start"] = self.start_time.to_text()
        elm.attrib["auto_fit"] = "{0}".format(int(self.auto_fit_duration))
        elm.attrib["note"] = "{0}".format(self.music_note)
        if self.midi_channel is not None:
            elm.attrib["mchannel"] = "{0}".format(self.midi_channel)
            elm.attrib["mvelocity"] = "{0}".format(self.midi_velocity)
        if self.instru:
            elm.attrib["instru"] = self.instru.get_name()
        return elm

    def load_from_xml(self, elm):
        self.y = float(elm.attrib.get("y"))
        self.name = elm.attrib.get("name", self.name)
        self.loop = int(elm.attrib.get("loop"))
        self.duration_time = AudioBlockTime.from_text(elm.attrib.get("duration"))
        self.start_time = AudioBlockTime.from_text(elm.attrib.get("start"))
        self.auto_fit_duration = bool(int(elm.attrib.get("auto_fit")))
        self.duration = self.duration_time.sample_count
        if elm.attrib.get("mchannel"):
            self.midi_channel = int(elm.attrib.get("mchannel"))
            self.midi_velocity = int(elm.attrib.get("mvelocity"))

    def recompute_time(self, beat):
        self.duration_time.recompute(beat)
        self.duration = self.duration_time.sample_count
        self.start_time.recompute(beat)

    def __eq__(self, other):
        return isinstance(other, AudioBlock) and other.id_num == self.id_num

    def __hash__(self):
        return hash(("audio_block", self.id_num))

    def set_owner(self, owner):
        self.owner = owner

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

    def set_y(self, y):
        self.y = y

    def set_loop(self, loop):
        self.loop = loop

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

    def destroy(self):
        if self.instru:
            self.instru.remove_block(self)
        if self.owner:
            self.owner.remove_block(self)

    def get_instru_set(self):
        if self.instru:
            return set([self.instru])
        return None

    @staticmethod
    def get_blank_data(sample_count):
        return numpy.zeros((sample_count, AudioBlock.ChannelCount), dtype=numpy.float32)


