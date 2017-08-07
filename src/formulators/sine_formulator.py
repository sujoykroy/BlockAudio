import numpy
import math
import scipy.interpolate

class SineFormulator(object):
    def __init__(self):
        pass

    def get_rounded_duration(self, note, base_note, base_duration):
        factor = note.frequency/base_note.frequency
        period = 1/note.frequency
        duration = round((base_duration*factor)/period)*period
        return duration

    def get_note_samples(self, note, base_note, base_duration, channel_count, sample_rate):
        duration = self.get_rounded_duration(note, base_note, base_duration)
        t = numpy.arange(0, duration, 1./sample_rate)
        samples = numpy.sin(2*math.pi*note.frequency*t)

        seg = 5
        env_x = [t[0], t[seg/2], t[seg], t[-seg], t[-seg/2], t[-1]]
        env_y =  [0, .5, .9, .9, .5, 0]
        interp = scipy.interpolate.interp1d(env_x, env_y, bounds_error=False, kind="linear")
        env = interp(t)
        print samples.shape, env.shape
        samples = env #numpy.multiply(samples, env)

        return samples
