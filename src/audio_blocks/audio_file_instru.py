from audio_samples_instru import AudioSamplesInstru
from audio_file_block import AudioFileBlock

class AudioFileInstru(AudioSamplesInstru):
    def __init__(self, filename, sample_count=None):
        self.filename = filename
        self.base_block = AudioFileBlock(filename, sample_count)
        AudioSamplesInstru.__init__(
                    self,
                    self.base_block.get_full_samples(),
                    self.base_block.music_note)

