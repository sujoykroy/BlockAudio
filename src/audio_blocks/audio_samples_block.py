import numpy
from audio_block import AudioBlock

class AudioSamplesBlock(AudioBlock):
    def __init__(self, samples):
        super(AudioSamplesBlock, self).__init__()
        self.samples = samples
        self.duration = samples.shape[0]
        self.inclusive_duration = self.duration

    def get_samples(self, frame_count, start_from=None, use_loop=True, loop=None):
        if self.paused:
            return None

        if start_from is None:
            start_pos = self.current_pos
        else:
            start_pos = start_from

        if loop is None:
            loop = self.loop

        data = None
        if loop and use_loop:
            spread = frame_count
            read_pos = start_pos
            while data is None or data.shape[0]<frame_count:
                if loop == self.LOOP_STRETCH:
                    if start_pos>=self.duration:
                        break
                    read_pos = start_pos%self.samples.shape[0]
                else:
                    start_pos %= self.duration
                    read_pos = start_pos
                seg = self.samples[read_pos: read_pos+spread, :]
                if data is None:
                    data = seg
                else:
                    data = numpy.append(data, seg, axis=0)

                start_pos += seg.shape[0]
                spread -= seg.shape[0]

            if start_from is None:
                self.current_pos = start_pos
        else:
            data = self.samples[start_pos: start_pos+frame_count, :]
            if start_from is None:
                self.current_pos = start_pos + data.shape[0]

        if data.shape[0]<frame_count:
            blank_shape = (frame_count - data.shape[0], AudioBlock.ChannelCount)
            data = numpy.append(data, numpy.zeros(blank_shape, dtype=numpy.float32), axis=0)
        return data
