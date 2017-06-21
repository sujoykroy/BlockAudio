from moviepy.editor import *
import random, numpy

def get_random_segment(samples, min_size, max_size):
    min_size = int(min_size)
    max_size = int(max_size)
    random.seed(random.random())
    start_at = min(int(samples.shape[0]*random.random()), samples.shape[0]-min_size-1)
    segment_size = min(max(int((samples.shape[0]-start_at)*random.random()), min_size), max_size-1)
    end_at = min(start_at+segment_size+1, samples.shape[0])
    if random.choice([True, False]):
        start_at, end_at = end_at, start_at
    return (start_at, end_at)

class SamplesAudioClip(AudioClip):
    def __init__(self, samples, sample_rate):
        AudioClip.__init__(self, make_frame=None, duration=samples.shape[0]/float(sample_rate))
        self.samples = samples
        self.sample_rate = sample_rate
        self.nchannels = samples.shape[1]

    def make_frame(self, t):
        return self.samples[(t*self.sample_rate).astype(numpy.uint32), :]

    def save_as(self, filename):
        self.write_audiofile(filename, fps=self.sample_rate)

def build_samples_From_segment_ranges(samples, segment_ranges):
    final_samples = None
    for start_at, end_at in segment_ranges:
        if start_at>end_at:
            step = -1
        else:
            step = 1
        selected_samples = samples[start_at:end_at:step, :]
        if final_samples is None:
            final_samples = selected_samples
        else:
            final_samples = numpy.concatenate((final_samples, selected_samples), axis=0)
    return final_samples

def mix_it_up(audio_filename, save_filename, min_time, max_time, segment_count):
    if max_time is None:
        max_time = min_time

    audio_clip = AudioFileClip(audio_filename)
    audio_samples = audio_clip.to_soundarray(buffersize=1000)

    segment_ranges = []
    for i in range(segment_count):
        start_at, end_at = get_random_segment(audio_samples,
                    audio_clip.fps*min_time, audio_clip.fps*max_time)
        segment_ranges.append((start_at, end_at))

    built_samples = build_samples_From_segment_ranges(audio_samples, segment_ranges)
    del audio_samples

    new_audio_clip = SamplesAudioClip(built_samples, audio_clip.fps)
    new_audio_clip.save_as(save_filename)
    print "Final audio duration is ", new_audio_clip.duration, "sec"


mix_it_up(
    "/home/sujoy/Music/Works/Flops.ogg",
    "/home/sujoy/Temporary/mixed.ogg",
    min_time=6,
    max_time=None,
    segment_count=60
)
