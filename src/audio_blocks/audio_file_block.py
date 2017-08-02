import time, numpy
import moviepy.editor as movie_editor
from audio_block import AudioBlock
from audio_samples_block import AudioSamplesBlock

class AudioFileBlockCache(object):
    TotalMemory = 0
    Files = dict()
    AccessTimeList = []
    MEMORY_LIMIT = 500*1024*1024

class AudioFileBlock(AudioSamplesBlock):
    def __init__(self, filename):
        AudioSamplesBlock.__init__(self, samples=AudioBlock.get_blank_data(1))

        self.filename = filename
        self.last_access_at = None
        self.calculate_duration()
        self.samples_loaded = False
        AudioFileBlockCache.Files[self.filename] = self

    def calculate_duration(self):
        audioclip = movie_editor.AudioFileClip(self.filename)
        self.duration = int(audioclip.duration*AudioBlock.SampleRate)
        return self.duration

    def load_samples(self):
        self.last_access_at = time.time()
        if self.samples_loaded:
            return
        audioclip = movie_editor.AudioFileClip(self.filename)
        try:
            self.samples = audioclip.to_soundarray(buffersize=1000).astype(numpy.float32)
        except IOError as e:
            self.samples = numpy.zeros((0, AudioBlock.ChannelCount), dtype=numpy.float32)

        AudioFileBlockCache.TotalMemory  += self.samples.nbytes
        self.samples_loaded = True

    def unload_samples(self):
        if not self.samples_loaded:
            return

        AudioFileBlockCache.TotalMemory -= self.samples.nbytes
        self.samples = AudioBlock.get_blank_data(1)
        self.samples_loaded = True

    def get_samples(self, frame_count, start_from=None, use_loop=True):
        if not self.samples_loaded:
            self.load_samples()
            self.clean_memory(exclude=self)
        return AudioSamplesBlock.get_samples(
                self, frame_count, start_from=start_from, use_loop=use_loop)

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
