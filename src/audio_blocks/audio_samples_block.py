import numpy
from audio_block import AudioBlock
from ..commons import AudioMessage
import moviepy.editor as movie_editor
import scipy.io.wavfile

class AudioSamplesBlock(AudioBlock):
    TYPE_NAME = "samples"

    def __init__(self, samples):
        super(AudioSamplesBlock, self).__init__()
        self.samples = samples
        self.set_sample_count(samples.shape[0])
        self.inclusive_duration = self.duration

    def copy(self):
        if self.instru:
            newob = self.instru.create_note_block(self.music_note)
        else:
            newob = type(self)(self.samples.copy())
        self.copy_values_into(newob)
        return newob

    @classmethod
    def create_from_xml(cls, elm, instru):
        music_note = elm.get("note")
        newob = instru.create_note_block(music_note)
        newob.load_from_xml(elm)
        return newob

    def readjust(self):
        if self.auto_fit_duration:
            self.set_sample_count(self.samples.shape[0])
        self.inclusive_duration = self.samples.shape[0]

    def set_samples(self, samples):
        self.samples = samples
        self.readjust()

    def get_samples(self, frame_count, start_from=None, use_loop=True, loop=None):
        if self.paused:
            return None
        if start_from is None:
            start_pos = self.current_pos
        else:
            start_pos = start_from

        if loop is None or self.loop == self.LOOP_NEVER_EVER:
            loop = self.loop

        audio_message = AudioMessage()
        data = None

        if loop and loop != self.LOOP_NEVER_EVER and use_loop:
            spread = frame_count
            start_init_pos = start_pos
            elapsed_pos = 0
            while data is None or data.shape[0]<frame_count:
                if loop == self.LOOP_STRETCH:
                    if start_pos>=self.duration:
                        break
                    read_pos = start_pos%self.samples.shape[0]
                else:
                    start_pos %= self.duration
                    read_pos = start_pos

                if read_pos<self.inclusive_duration:
                    if self.midi_channel is not None:
                        if read_pos == 0:
                            audio_message.midi_messages.append(
                                self.new_midi_note_on_message(elapsed_pos))

                    seg = self.samples[read_pos: read_pos+spread, :]
                else:
                    read_count = min(self.duration-start_pos, spread)
                    seg = numpy.zeros((read_count, self.ChannelCount), dtype=numpy.float32)

                if data is None:
                    data = seg
                else:
                    data = numpy.append(data, seg, axis=0)

                start_pos += seg.shape[0]
                spread -= seg.shape[0]
                elapsed_pos += seg.shape[0]

                if self.midi_channel is not None:
                    if start_pos%self.inclusive_duration ==0:
                        audio_message.midi_messages.append(
                            self.new_midi_note_off_message(elapsed_pos))

            if data is None:
                data = numpy.zeros((frame_count, self.ChannelCount), dtype=numpy.float32)
            if start_from is None:
                self.lock.acquire()
                self.current_pos = start_pos
                self.lock.release()
        else:
            if self.midi_channel is not None and start_pos == 0:
                audio_message.midi_messages.append(self.new_midi_note_on_message(0))
            if start_pos>=self.duration:
                data = numpy.zeros((0, AudioBlock.ChannelCount))
            else:
                data = self.samples[start_pos: start_pos+frame_count, :]
            start_pos += data.shape[0]
            if self.midi_channel is not None and start_pos == self.duration and data.shape[0]>0:
                audio_message.midi_messages.append(self.new_midi_note_off_message(data.shape[0]))
            if start_from is None:
                self.lock.acquire()
                self.current_pos = start_pos
                self.lock.release()

        if data.shape[0]<frame_count:
            blank_shape = (frame_count - data.shape[0], AudioBlock.ChannelCount)
            data = numpy.append(data, numpy.zeros(blank_shape, dtype=numpy.float32), axis=0)
        audio_message.samples = data
        audio_message.block_positions.append((self, start_pos))
        return audio_message

    def save_to_file(self, filename):
        scipy.io.wavfile.write(filename, int(AudioBlock.SampleRate), self.samples)
        return
        clip = movie_editor.AudioClip(self.make_audio_frame, duration=self.get_time_duration())
        #clip = movie_editor.AudioArrayClip(self.samples, fps=AudioBlock.SampleRate)
        clip.write_audiofile(filename, fps=int(AudioBlock.SampleRate))
        del clip

    def make_audio_frame(self, t):
        t = (t*AudioBlock.SampleRate)
        if isinstance(t, numpy.ndarray):
           t = (numpy.round(t)).astype(numpy.int32)
        else:
            t = int(round(t))
        return self.samples[t, :]
