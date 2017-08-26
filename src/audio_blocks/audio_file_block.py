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
        self.set_filename(filename)
        self.mult = 1.

    def __mul__(self, other):
        newob = AudioFileClipSamples(self.filename)
        newob.mult = other
        return newob

    def set_filename(self, filename):
        self.filename = filename
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
                return samples[start_key, end_key]*self.mult
            else:
                samples = self.mult*audioclip.get_frame(start_key*1./AudioBlock.SampleRate)
                return samples[end_key]
        else:
            raise IndexError()

class AudioFileBlock(AudioSamplesBlock):
    MAX_DURATION_SECONDS = 5*60

    def __init__(self, filename, sample_count=None, preload=True):
        AudioSamplesBlock.__init__(self, samples=AudioBlock.get_blank_data(1))
        self.sample_count = sample_count
        self.filename = filename
        self.last_access_at = None
        self.preload = preload
        self.samples_loaded = False
        self.calculate_duration()
        self.set_sample_count(self.inclusive_duration)

    def set_filename(self, filename):
        self.unload_samples()
        self.remove_from_cache()

        self.filename = filename
        if isinstance(self.samples, AudioFileClipSamples):
            self.samples.set_filename(filename)
        else:
            self.calculate_duration()
            self.set_sample_count(self.inclusive_duration)
            AudioFileBlockCache.Files[self.filename] = self

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

    def readjust(self):
        self.set_filename(self.filename)

    def load_samples(self):
        if self.samples_loaded:
            return

        self.last_access_at = time.time()
        audioclip = self.get_audio_clip()

        if self.preload and audioclip.duration<self.MAX_DURATION_SECONDS:
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

            AudioFileBlockCache.Files[self.filename] = self
            AudioFileBlockCache.TotalMemory  += self.samples.nbytes
            self.clean_memory(exclude=self)
        else:
            self.samples = AudioFileClipSamples(self.filename)
        self.samples_loaded = True

    def get_full_samples(self):
        self.load_samples()
        return self.samples

    def unload_samples(self):
        if not self.samples_loaded:
            return

        if not isinstance(self.samples, AudioFileClipSamples):
            AudioFileBlockCache.TotalMemory -= self.samples.nbytes
        self.samples = AudioBlock.get_blank_data(1)
        self.samples_loaded = False

    def get_samples(self, frame_count, start_from=None, use_loop=True, loop=None):
        self.load_samples()
        return AudioSamplesBlock.get_samples(
                self, frame_count, start_from=start_from, use_loop=use_loop, loop=loop)

    def get_description(self):
        return self.name

    def remove_from_cache(self):
        if self.filename in AudioFileBlockCache.Files:
            del AudioFileBlockCache.Files[self.filename]
        self.last_access_at = None

    def destroy(self):
        self.unload_samples()
        self.remove_from_cache()
        super(AudioSamplesBlock, self).destroy()

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
