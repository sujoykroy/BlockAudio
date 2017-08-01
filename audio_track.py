import numpy

class AudioTrack(object):
    FramePerBuffer = 1024
    SampleRate = 44100.
    ChannelCount = 2

    def __init__(self):
        self.paused = True
        self.loop = True
        self.duration = 0
        self.current_pos = 0

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def calculate_duration(self):
        return self.duration

    def get_samples(self, frame_count, start_from=None, use_loop=True):
        return self.get_blank_data(frame_count)

    @staticmethod
    def get_blank_data(sample_count):
        return numpy.zeros((sample_count, AudioTrack.ChannelCount), dtype=numpy.float32)

