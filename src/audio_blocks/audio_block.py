import numpy
import time
from ..commons import MidiMessage, AudioMessage

class AudioBlock(object):
    FramesPerBuffer = 1024
    SampleRate = 44100.
    ChannelCount = 2
    LOOP_NONE = 0
    LOOP_INFINITE = 1
    LOOP_STRETCH = 2

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
        self.duration = 0
        self.inclusive_duration = 0
        self.current_pos = 0
        self.music_note = "C5"
        self.midi_channel = None
        self.midi_velocity = 64
        self.play_pos = 0

        self.id_num = AudioBlock.IdSeed
        AudioBlock.IdSeed += 1
        self.name = self.new_name()

    def set_music_note(self, note):
        self.music_note = note

    def set_midi_channel(self, channel):
        self.midi_channel = channel

    def set_note(self, note):
        self.music_note = note

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

    def set_duration(self, duration):
        if duration<=0:
            return
        self.duration = duration

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
        return self.duration

    def get_time_duration(self):
        return self.duration/AudioBlock.SampleRate

    def get_samples(self, frame_count, start_from=None, use_loop=True, loop=None):
        return AudioMessage(self.get_blank_data(frame_count))

    def get_description(self):
        return self.name

    @staticmethod
    def get_blank_data(sample_count):
        return numpy.zeros((sample_count, AudioBlock.ChannelCount), dtype=numpy.float32)


