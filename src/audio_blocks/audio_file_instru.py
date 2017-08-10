from audio_samples_instru import AudioSamplesInstru
from audio_file_block import AudioFileBlock
import moviepy.editor as moviepy_editor
import os

class AudioFileInstru(AudioSamplesInstru):
    def __init__(self, filename, sample_count=None):
        self.filename = filename
        self.sample_count = sample_count
        AudioSamplesInstru.__init__(
                    self,
                    None)
        self.set_name(os.path.basename(filename))

    def create_note_block(self, note="C5"):
        if self.samples is None:
            self.base_block = AudioFileBlock(self.filename, self.sample_count)
            self.samples = self.base_block.get_full_samples()
        return super(AudioFileInstru, self).create_note_block(note)

    @classmethod
    def load(cls, filepath, prefix='', recursive=True, test=False):
        if os.path.isdir(filepath):
            instru_list = []
            for filename in os.listdir(filepath):
                child_path = os.path.join(filepath, filename)
                if os.path.isdir(child_path):
                    if not recursive:
                        continue
                    else:
                        child_prefix = prefix + filename + "/"
                else:
                    child_prefix = prefix
                instru = cls.load(child_path, prefix=child_prefix)
                if instru:
                    instru_list.extend(instru)
            return instru_list
        if test:
            try:
                clip = moviepy_editor.AudioFileClip(filepath)
            except:
                clip = None
        else:
            clip = None
        if not test or (clip and clip.duration>0):
            del clip
            instru = AudioFileInstru(filepath)
            instru.set_name(prefix + os.path.basename(filepath))
            return [instru]
        return None
