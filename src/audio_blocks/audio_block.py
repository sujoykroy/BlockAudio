import numpy
import time

class AudioBlock(object):
    FramesPerBuffer = 1024
    SampleRate = 44100.
    ChannelCount = 2

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
        self.loop = True
        self.duration = 0
        self.current_pos = 0
        self.id_num = AudioBlock.IdSeed
        AudioBlock.IdSeed += 1
        self.name = self.new_name()

    def get_id(self):
        return self.id_num

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def calculate_duration(self):
        return self.duration

    def get_time_duration(self):
        return self.duration/AudioBlock.SampleRate

    def get_samples(self, frame_count, start_from=None, use_loop=True):
        return self.get_blank_data(frame_count)

    def get_description(self):
        return self.name

    @staticmethod
    def get_blank_data(sample_count):
        return numpy.zeros((sample_count, AudioBlock.ChannelCount), dtype=numpy.float32)


