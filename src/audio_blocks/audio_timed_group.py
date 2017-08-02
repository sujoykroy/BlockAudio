from audio_block import AudioBlock
import threading
import time
import numpy

class AudioTimedGroup(AudioBlock):
    def __init__(self):
        super(AudioTimedGroup, self).__init__()
        self.blocks = []
        self.blocks_positions = dict()

        self.lock = threading.RLock()
        self.blank_data = self.get_blank_data(AudioBlock.FramesPerBuffer)

    def add_block(self, block, at, stretch=True, sample_unit=False):
        ret = True
        self.lock.acquire()
        if not sample_unit:
            at = at*AudioBlock.SampleRate
        at = int(at)
        if block not in self.blocks:
            self.blocks.append(block)
        else:
            ret = False
        self.blocks_positions[block.get_id()]=at
        self.lock.release()
        if stretch:
            self.calculate_duration()
        return ret

    def remove_block(self, block, stretch=True):
        self.lock.acquire()
        if block in self.blocks:
            index = self.blocks.index(block)
            del self.blocks[index]
            del self.blocks_positions[block.get_id()]
        self.lock.release()
        if stretch:
            self.calculate_duration()

    def get_block_position(self, block):
        return self.blocks_positions.get(block.get_id(), -1)

    def calculate_duration(self):
        self.lock.acquire()
        block_count = len(self.blocks)
        self.lock.release()

        duration = 0
        for i in xrange(block_count):
            self.lock.acquire()
            if i<len(self.blocks):
                block = self.blocks[i]
                block_start_pos = self.blocks_positions[block.get_id()]
            else:
                block = None
            self.lock.release()

            if not block:
                break

            end_at = self.blocks_positions[block.get_id()]+block.calculate_duration()
            if end_at>duration:
                duration = end_at
        self.duration = duration
        return duration

    def get_samples(self, frame_count, start_from=None, use_loop=True):
        if self.paused:
            return self.blank_data
        self.lock.acquire()
        block_count = len(self.blocks)
        self.lock.release()
        if start_from is None:
            start_pos = self.current_pos
        else:
            start_pos = int(start_from)

        if self.loop and use_loop:
            data = None

            while data is None or data.shape[0]<frame_count:
                sub_frame_count = min(self.duration-start_pos, frame_count)
                seg = self.get_samples(sub_frame_count, start_from=start_pos, use_loop=False)
                if data is None:
                    data = seg
                else:
                    data = numpy.append(data, seg, axis=0)
                start_pos += seg.shape[0]
                start_pos %= self.duration

            if start_from is None:
                self.current_pos = start_pos
            return data

        samples = None
        for i in xrange(block_count):
            block_samples = None
            self.lock.acquire()
            if i<len(self.blocks):
                block = self.blocks[i]
                block_start_pos = self.blocks_positions[block.get_id()]
            else:
                block = None
            self.lock.release()

            if not block:
                break
            if start_pos+frame_count<block_start_pos:
                continue

            if block.loop:
                if block_start_pos<start_pos:
                    elapsed = start_pos-block_start_pos
                    block_start_pos += (elapsed//block.duration)*block.duration
                    block_start_pos = int(block_start_pos)
            elif block_start_pos+block.duration<start_pos:
                continue

            if block_start_pos>start_pos:
                block_samples = self.blank_data[:block_start_pos-start_pos, :]
                block_start_from = 0
                sub_frame_count = start_pos + frame_count-block_start_pos
            else:
                block_samples = None
                block_start_from = start_pos-block_start_pos
                sub_frame_count = frame_count

            seg = block.get_samples(sub_frame_count, start_from=block_start_from)

            if block_samples is None:
                block_samples = seg
            else:
                block_samples = numpy.append(block_samples, seg, axis=0)

            if samples is None:
                samples = block_samples
            else:
                samples  = samples + block_samples

        if  samples is None:
            samples = self.blank_data[:frame_count, :]

        if start_from is None:
            self.current_pos = start_pos + frame_count
            if self.current_pos>self.duration:
                self.current_pos = self.duration

        return samples
