import time, numpy
import moviepy.editor as movie_editor
from audio_block import AudioBlock
from audio_samples_block import AudioSamplesBlock

class AudioFileBlockCache(object):
    TotalMemory = 0
    Files = dict()
    AccessTimeList = []
    MEMORY_LIMIT = 500*1024*1024

class AudioFileClipSamples(object):
    def __init__(self, filename):
        self.audioclip = movie_editor.AudioFileClip(filename)
        sample_count = int(round(self.audioclip.duration*AudioBlock.SampleRate))
        self.shape = (sample_count, self.audioclip.nchannels)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            start_key = key[0]
            end_key = key[1]
            audioclip = self.audioclip
            if isinstance(start_key, slice):
                if start_key.start:
                    start_at = start_key.start*1./AudioBlock.SampleRate
                else:
                    start_at = 0

                if start_at>=self.audioclip.duration:
                    return numpy.zeros((0, self.audioclip.nchannels), dtype=numpy.float32)

                if start_key.stop:
                    end_at = start_key.stop*1./AudioBlock.SampleRate
                    if end_at>self.audioclip.duration:
                        end_at = self.audioclip.duration
                else:
                    end_at = None

                start_key = slice(None, None, start_key.step)
                audioclip = self.audioclip.subclip(start_at, end_at)
                samples = audioclip.to_soundarray(buffersize=1000).astype(numpy.float32)
                return samples[start_key, end_key]
            else:
                samples = audioclip.get_frame(start_key*1./AudioBlock.SampleRate)
                return samples[end_key]
        else:
            raise IndexError()

class AudioFileBlock(AudioSamplesBlock):
    MAX_DURATION_SECONDS = 10*60

    def __init__(self, filename, sample_count=None, preload=True):
        AudioSamplesBlock.__init__(self, samples=AudioBlock.get_blank_data(1))
        self.sample_count = sample_count
        self.filename = filename
        self.last_access_at = None
        self.preload = preload
        if not self.preload:
            self.samples_loaded = True
            self.samples = AudioFileClipSamples(self.filename)
        else:
            self.samples_loaded = False
            AudioFileBlockCache.Files[self.filename] = self
        self.calculate_duration()
        self.set_sample_count(self.inclusive_duration)

    def get_audio_clip(self):
        audioclip = movie_editor.AudioFileClip(self.filename)
        if self.preload and audioclip.duration>self.MAX_DURATION_SECONDS:
            audioclip = audioclip.set_duration(self.MAX_DURATION_SECONDS)
        return audioclip

    def calculate_duration(self):
        if self.sample_count:
            self.inclusive_duration = self.sample_count
        else:
            audioclip = self.get_audio_clip()
            self.inclusive_duration = int(audioclip.duration*AudioBlock.SampleRate)

    def load_samples(self):
        if not self.preload:
            return
        if self.samples_loaded:
            return

        self.last_access_at = time.time()
        audioclip = self.get_audio_clip()
        try:
            self.samples = audioclip.to_soundarray(buffersize=1000).astype(numpy.float32)
        except IOError as e:
            self.samples = numpy.zeros((0, AudioBlock.ChannelCount), dtype=numpy.float32)

        if self.sample_count:
            self.samples = self.samples[:self.sample_count, :]
            if self.samples.shape[0]<self.sample_count:
                blank_count = self.sample_count-self.samples.shape[0]
                blank_data = numpy.zeros((blank_count, self.samples.shape[1]), dtype=numpy.float32)
                self.samples = numpy.append(self.samples, blank_data, axis=0)

        AudioFileBlockCache.TotalMemory  += self.samples.nbytes
        self.samples_loaded = True
        self.clean_memory(exclude=self)

    def get_full_samples(self):
        self.load_samples()
        return self.samples

    def unload_samples(self):
        if not self.samples_loaded:
            return

        AudioFileBlockCache.TotalMemory -= self.samples.nbytes
        self.samples = AudioBlock.get_blank_data(1)
        self.samples_loaded = True

    def get_samples(self, frame_count, start_from=None, use_loop=True, loop=None):
        if self.preload:
            if not self.samples_loaded:
                self.load_samples()
        return AudioSamplesBlock.get_samples(
                self, frame_count, start_from=start_from, use_loop=use_loop, loop=loop)

    def get_description(self):
        return self.name

    @staticmethod
    def clean_memory(exclude):
        sorted_files = sorted(AudioFileBlockCache.Files.values(),
                                key=lambda cache: cache.last_access_at)
        while sorted_files and AudioFileBlockCache.TotalMemory>AudioFileBlockCache.MEMORY_LIMIT:
            first_file = sorted_files[0]
            if exclude and first_file.filename == exclude.filename:
                continue
            sorted_files = sorted_files[1:]
            first_file.unload_samples()
