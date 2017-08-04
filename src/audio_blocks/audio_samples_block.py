import numpy
from audio_block import AudioBlock
from ..commons import AudioMessage

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

        audio_message = AudioMessage()
        data = None
        if self.midi_channel is not None and start_pos == 0:
            audio_message.midi_messages.append(self.new_midi_note_on_message(0))

        if loop and use_loop:
            spread = frame_count
            start_init_pos = start_pos
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

                if self.midi_channel is not None:
                    remainder = (start_init_pos+data.shape[0])%self.inclusive_duration
                    quotient = (start_init_pos+data.shape[0])//self.inclusive_duration
                    for q in xrange(quotient):
                        audio_message.midi_messages.append(self.new_midi_note_off_message(
                            q*self.inclusive_duration-start_init_pos))
                        if remainder>0:
                            audio_message.midi_messages.append(self.new_midi_note_on_message(
                                q*self.inclusive_duration-start_init_pos))

            if data is None:
                data = numpy.zeros((frame_count, self.ChannelCount), dtype=numpy.float32)
            if start_from is None:
                self.current_pos = start_pos
        else:
            data = self.samples[start_pos: start_pos+frame_count, :]
            start_pos += data.shape[0]
            if self.midi_channel is not None and start_pos == self.duration and data.shape[0]>0:
                audio_message.midi_messages.append(self.new_midi_note_off_message(data.shape[0]))
            if start_from is None:
                self.current_pos = start_pos

        if data.shape[0]<frame_count:
            blank_shape = (frame_count - data.shape[0], AudioBlock.ChannelCount)
            data = numpy.append(data, numpy.zeros(blank_shape, dtype=numpy.float32), axis=0)
        audio_message.samples = data
        audio_message.block_positions.append((self, start_pos))
        return audio_message
