class Beat(object):
    def __init__(self, bpm, sample_rate, pixel_per_sample):
        self.bpm = bpm
        self.sample_rate = sample_rate
        self.pixel_per_sample = pixel_per_sample
        self.div_per_beat = 4
        self.calculate()

    def set_bpm(self, bpm):
        self.bpm = bpm
        self.calculate()

    def set_div_per_beat(self, value):
        self.div_per_beat = int(value)
        self.calculate()

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
        self.calculate()

    def set_pixel_per_sample(self, pixel_per_sample):
        self.pixel_per_sample = pixel_per_sample
        self.calculate()

    def calculate(self):
        self.beat_sample_unit = ((60./self.bpm)*self.sample_rate)
        self.div_sample_unit = self.beat_sample_unit/self.div_per_beat
        self.div_pixel_unit = self.div_sample_unit*self.pixel_per_sample
        self.beat_pixel_unit = self.div_pixel_unit*self.div_per_beat

    def pixel2sample(self, pixel):
        sample = pixel*1./self.pixel_per_sample
        sample = (sample//self.div_sample_unit)*self.div_sample_unit
        return int(round(sample))

    def get_beat_time(self, beat):
        return beat*self.beat_sample_unit*1./self.sample_rate

    def get_beat_sample(self, beat):
        return beat*self.beat_sample_unit

    def get_div_time(self, div):
        return div*self.beat_sample_unit*1./(self.div_per_beat*self.sample_rate)

    def get_div_sample(self, div):
        return int(div*self.beat_sample_unit*1./(self.div_per_beat))

    def get_beat_pixels(self, start_pixel, end_pixel, spread):
        beat_index = max((start_pixel//self.beat_pixel_unit)-1, 0)
        start_pixel = beat_index*self.beat_pixel_unit
        pixel = start_pixel
        mult = int(spread*1./self.beat_pixel_unit)
        if mult<=0:
            mult = 1
        while pixel<end_pixel:
            yield int(beat_index), pixel
            pixel += self.beat_pixel_unit*mult
            beat_index += mult

    def get_div_pixels(self, start_pixel, end_pixel, spread):
        start_pixel = max((start_pixel//self.div_pixel_unit)-1, 0)*self.div_pixel_unit
        pixel = start_pixel
        mult = int(spread*1./self.beat_pixel_unit)
        if mult<=0:
            mult = 1
        while pixel<end_pixel:
            yield pixel
            pixel += self.div_pixel_unit*mult

