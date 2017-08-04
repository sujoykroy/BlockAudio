from audio_block import AudioBlock
import threading
import time
import numpy
from ..commons import AudioMessage

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
        self.calculate_duration()
        if stretch:
            self.duration = self.inclusive_duration
        return ret

    def remove_block(self, block, stretch=True):
        self.lock.acquire()
        if block in self.blocks:
            index = self.blocks.index(block)
            del self.blocks[index]
            del self.blocks_positions[block.get_id()]
        self.lock.release()
        self.calculate_duration()
        if stretch:
            self.duration = self.inclusive_duration

    def set_block_name(self, block, name):
        for existing_block in self.blocks:
            if existing_block.get_name() == name:
                return False
        block.set_name(name)

    def get_block_position(self, block):
        return self.blocks_positions.get(block.get_id(), -1)

    def set_block_at(self, block, pos):
        self.lock.acquire()
        self.blocks_positions[block.get_id()] = pos
        self.lock.release()

    def stretch_block_to(self, block, end_pos):
        self.lock.acquire()
        start_pos = self.blocks_positions[block.get_id()]
        block.set_duration(end_pos-start_pos)
        self.lock.release()

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

            end_at = self.blocks_positions[block.get_id()]+block.duration
            if end_at>duration:
                duration = end_at
        self.inclusive_duration = duration

    def get_samples(self, frame_count, start_from=None, use_loop=True, loop=None):
        if self.paused:
            return self.blank_data
        self.lock.acquire()
        block_count = len(self.blocks)
        self.lock.release()
        if start_from is None:
            start_pos = self.current_pos
        else:
            start_pos = int(start_from)

        if loop is None:
            loop = self.loop

        audio_message = AudioMessage()
        if loop and use_loop:
            data = None
            spread = frame_count
            data_count = 0
            while data is None or data.shape[0]<frame_count:
                if loop == self.LOOP_STRETCH:
                    if start_pos>=self.duration:
                        break
                    read_pos = start_pos%self.inclusive_duration
                else:
                    start_pos %= self.inclusive_duration
                    read_pos = start_pos

                if read_pos+spread>self.inclusive_duration:
                    read_count = self.inclusive_duration-read_pos
                else:
                    read_count = spread
                seg_message = self.get_samples(read_count, start_from=read_pos, use_loop=False)
                if seg_message.midi_messages:
                    for midi_message in seg_message.midi_messages:
                        midi_message.increase_delay(data_count)
                    audio_message.midi_messages.extend(seg_message.midi_messages)
                if seg_message.block_positions:
                    audio_message.block_positions.extend(seg_message.block_positions)

                seg_samples = seg_message.samples
                if data is None:
                    data = seg_samples
                else:
                    data = numpy.append(data, seg_samples, axis=0)
                start_pos += seg_samples.shape[0]
                data_count += seg_samples.shape[0]
                spread -= seg_samples.shape[0]

            if start_from is None:
                self.current_pos = start_pos

            if data.shape[0]<frame_count:
                blank_shape = (frame_count - data.shape[0], AudioBlock.ChannelCount)
                data = numpy.append(data, numpy.zeros(blank_shape, dtype=numpy.float32), axis=0)

            audio_message.block_positions.append([self, start_pos])
            audio_message.samples = data
            return audio_message

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

            if block.loop == self.LOOP_INFINITE:
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

            seg_message = block.get_samples(sub_frame_count, start_from=block_start_from)
            if seg_message.midi_messages:
                audio_message.midi_messages.extend(seg_message.midi_messages)
            if seg_message.block_positions:
                audio_message.block_positions.extend(seg_message.block_positions)

            if block_samples is None:
                block_samples = seg_message.samples
            else:
                block_samples = numpy.append(block_samples, seg_message.samples, axis=0)

            if samples is None:
                samples = block_samples
            else:
                samples  = samples + block_samples

        if  samples is None:
            samples = self.blank_data[:frame_count, :]

        start_pos += frame_count

        if start_from is None:
            self.current_pos = start_pos
            if self.current_pos>self.duration:
                self.current_pos = self.duration

        audio_message.block_positions.append([self, start_pos])
        audio_message.samples = samples
        return audio_message
