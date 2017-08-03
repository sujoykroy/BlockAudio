import threading
from audio_block import AudioBlock

class AudioGroup(AudioBlock):
    def __init__(self):
        super(AudioGroup, self).__init__()
        self.blocks = []

        self.lock = threading.RLock()
        self.blank_data = self.get_blank_data(AudioBlock.FramesPerBuffer)

    def add_block(self, block):
        self.lock.acquire()
        self.blocks.append(block)
        self.lock.release()
        block.play()

    def remove_block(self, block):
        self.lock.acquire()
        if block in self.blocks:
            self.blocks.remove(block)
        self.lock.release()

    def get_samples(self, frame_count):
        if self.paused:
            return self.blank_data.copy()
        self.lock.acquire()
        block_count = len(self.blocks)
        self.lock.release()

        self._samples = None
        for i in xrange(block_count):

            self.lock.acquire()
            if i <len(self.blocks):
                block = self.blocks[i]
            else:
                block = None
            self.lock.release()

            if not block:
                break

            block_samples = block.get_samples(frame_count, loop=self.LOOP_INFINITE)
            if block_samples is None:
                continue

            if self._samples is None:
                self._samples = block_samples.copy()
            else:
                self._samples = self._samples + block_samples

        if  self._samples is None:
            self._samples = self.blank_data.copy()
        return self._samples

