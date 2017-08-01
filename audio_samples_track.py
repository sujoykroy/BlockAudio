import numpy
from audio_track import AudioTrack

class AudioSamplesTrack(AudioTrack):
    def __init__(self, samples):
        super(AudioSamplesTrack, self).__init__()
        self.samples = samples
        self.duration = samples.shape[0]

    def get_samples(self, frame_count, start_from=None, use_loop=True):
        if self.paused:
            return None

        if start_from is None:
            start_pos = self.current_pos
        else:
            start_pos = start_from

        data = None
        if self.loop and use_loop:
            while data is None or data.shape[0]<frame_count:
                seg = self.samples[start_pos: start_pos+frame_count, :]
                if data is None:
                    data = seg
                else:
                    data = numpy.append(data, seg, axis=0)
                start_pos += seg.shape[0]
                start_pos %= self.duration

            if start_from is None:
                self.current_pos = start_pos
        else:
            data = self.samples[start_from: start_from+frame_count, :]
            if start_from is None:
                self.current_pos = start_pos + data.shape[0]
            if data.shape[0]<frame_count:
                blank_shape = (frame_count - data.shape[0], AudioTrack.ChannelCount)
            data = numpy.append(data, numpy.zero(blank_shape, dtype=numpy.float32), axis=0)

        return data
