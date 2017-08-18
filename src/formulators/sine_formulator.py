import numpy
import math
import scipy.interpolate

class SineFormulator(object):
    def __init__(self, instru):
        self.instru = instru

    def get_rounded_duration(self, note, base_note, base_duration):
        factor = note.frequency/base_note.frequency
        period = 1/note.frequency
        duration = round((base_duration*factor)/period)*period
        return duration

    def get_note_samples(self, note):
        sample_rate = self.instru.get_sample_rate()
        duration = self.instru.duration_time.sample_count*1./sample_rate
        #duration=2/note.frequency
        t = numpy.arange(0, duration, 1./sample_rate, dtype=numpy.float32)
        samples = numpy.sin(2*math.pi*note.frequency*t)
        return samples
        seg = int(round(sample_rate*base_duration*.01))
        env_x = [t[0], t[seg/2], t[seg], t[-seg], t[-seg/2], t[-1]]
        env_y =  [0, .5, 1, 1, .5, 0]
        interp = scipy.interpolate.interp1d(env_x, env_y, bounds_error=False, kind="linear")
        env = interp(t).astype(numpy.float32)
        samples = samples*env

        return samples

Formulator = SineFormulator
