import threading
from audio_block import AudioBlock
from ..commons import AudioMessage

class AudioGroup(AudioBlock):
    def __init__(self):
        super(AudioGroup, self).__init__()
        self.blocks = []

        self.lock = threading.RLock()
        self.blank_data = self.get_blank_data(AudioBlock.FramesPerBuffer)
        self.block_loop = self.LOOP_INFINITE

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
            return None
        self.lock.acquire()
        block_count = len(self.blocks)
        self.lock.release()

        self._samples = None
        audio_message = AudioMessage()

        for i in xrange(block_count):

            self.lock.acquire()
            if i <len(self.blocks):
                block = self.blocks[i]
            else:
                block = None
            self.lock.release()

            if not block:
                break

            block_message = block.get_samples(frame_count, loop=self.block_loop)
            if block_message is None:
                continue
            if block_message.midi_messages:
                audio_message.midi_messages.extend(block_message.midi_messages)
            if block_message.block_positions:
                audio_message.block_positions.extend(block_message.block_positions)

            block_samples = block_message.samples
            if block_samples is None:
                continue

            if self._samples is None:
                self._samples = block_samples.copy()
            else:
                self._samples = self._samples + block_samples

        if self._samples is not None and self._samples.shape[0]<frame_count:
            blank_count = frame_count - self._samples.shape[0]
            self._samples = numpy.append(
                self._samples, self.blank_data[blank_count, :].copy(), axis=0)
        audio_message.samples = self._samples
        return audio_message

