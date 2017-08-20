import numpy
import math
import scipy.interpolate

class SineFormulator(object):
    def __init__(self, instru):
        self.instru = instru
        self.amplitude = 1.
        self.exponent = 20.
        self.param_list = [
            ["amplitude", float, dict(min=0, max=100, step=.1)],
            ["exponent",  float, dict(min=10, max=1000, step=.1)]
        ]

    def get_rounded_duration(self, note, base_note, base_duration):
        factor = note.frequency/base_note.frequency
        period = 1/note.frequency
        duration = round((base_duration*factor)/period)*period
        return duration

    def get_note_samples(self, note):
        sample_rate = self.instru.get_sample_rate()
        duration = self.instru.duration_time.sample_count*1./sample_rate
        t = numpy.arange(0, duration, 1./sample_rate, dtype=numpy.float32)
        samples = numpy.sin(2*math.pi*note.frequency*t)
        samples = self.amplitude*samples/(numpy.exp(t*self.exponent))
        samples = numpy.clip(samples, -1, 1)
        return samples

Formulator = SineFormulator
