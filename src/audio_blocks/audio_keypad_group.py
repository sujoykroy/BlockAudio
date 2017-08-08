import threading
from audio_block import AudioBlock
from audio_group import AudioGroup
from audio_samples_block import AudioSamplesBlock
from ..commons import AudioMessage
import scipy.interpolate
import numpy

class AudioKeypadBlock(AudioSamplesBlock):
    def __init__(self, samples):
        super(AudioKeypadBlock, self).__init__(samples)
        self.loop = None

    def is_stopped(self):
        return self.current_pos >= self.duration

    def end_smooth(self):
        if self.is_stopped():
            return

        seg = min(self.duration-self.current_pos, 20)
        env_y =  [1, .5, 0]
        env_x = [0, seg*.5, seg-1]

        interp = scipy.interpolate.interp1d(env_x, env_y, bounds_error=False, kind="linear")
        xs = numpy.arange(0, seg)
        env = interp(xs).astype(numpy.float32)
        if len(self.samples.shape)>1:
            env = numpy.repeat(env, self.samples.shape[1]).reshape(-1, self.samples.shape[1])

        self.samples[self.current_pos:self.current_pos+seg, :] = \
            self.samples[self.current_pos:self.current_pos+seg, :].copy()*env
        self.duration = self.current_pos+seg
        self.inclusive_duration = self.current_pos+seg

class AudioKeypadGroup(AudioGroup):
    def __init__(self):
        super(AudioKeypadGroup, self).__init__()
        self.block_loop = None

    def add_samples(self, samples):
        block = AudioKeypadBlock(samples)
        self.add_block(block)
        return block

    def get_samples(self, frame_count, loop=None):
        self.lock.acquire()
        block_count = len(self.blocks)
        self.lock.release()
        #if block_count:
        #    print "AudioKeypadGroup", block_count
        for i in xrange(block_count):
            self.lock.acquire()
            if i <len(self.blocks):
                block = self.blocks[i]
            else:
                block = None
            self.lock.release()

            if not block:
                break

            self.lock.acquire()
            if block.is_stopped():
                del self.blocks[i]
            self.lock.release()

        audio_message = super(AudioKeypadGroup, self).get_samples(frame_count)
        return audio_message
