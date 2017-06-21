from audio_segment import AudioSegment
import numpy, math

class AudioRawSamples(AudioSegment):
    def __init__(self, samples, sample_rate):
        AudioSegment.__init__(self, start_at=0, duration=0)
        self.samples = samples
        self.sample_rate = sample_rate
        self.start_at_size = int(math.ceil(self.start_at*self.sample_rate))
        self.duration = samples.shape[1]*1.0/self.sample_rate

    def get_samples_in_between(self, start_time, end_time):
        st = int(start_time*self.sample_rate)
        et = min((end_time*self.sample_rate)+1, self.samples.shape[1])
        return self.samples[:, st:et]

    def get_samples_in_between_size(self, st, et):
        st = int(st)
        et = int(et)
        return self.samples[:, st:et]

    def get_index_of_time(self, t):
        index = int(t*self.sample_rate)
        index = max(0, index)
        index = min(index, self.samples.shape[1]-1)
        return index

    def get_x_min_max(self):
        return [0, self.duration]

    def get_y_min_max(self):
        return [-1.0, 1.0]

    def get_y_base(self):
        return 0.0

    def get_segment_count(self):
        return self.samples.shape[0]

    def get_sample_at_x(self, segment_index, x):
        x = int(x*self.sample_rate)
        if x<0 or x>=self.samples.shape[1]:
            return None
        return self.samples[segment_index, x]

    def get_start_at_size(self):
        return self.start_at_size

    def get_duration_size(self):
        return self.samples.shape[1]

    def get_tail_masked_samples(self, from_t):
        time_index = self.get_index_of_time(from_t)
        tail_count = (self.samples.shape[1]-time_index)
        if tail_count>0:
            diedown_mask = numpy.repeat(
                [numpy.linspace(1.0, 0, tail_count)], self.samples.shape[0], axis=0)
            diedown_mask.shape = (self.samples.shape[0], tail_count)
            samples = self.samples.copy()
            samples[:, -tail_count:] = samples[:, -tail_count:]*diedown_mask
            return samples
        return None
