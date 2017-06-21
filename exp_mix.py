from moviepy.editor import *
import random, numpy

def get_random_segment(samples, min_size, max_size, speeds):
    min_size = int(min_size)
    max_size = int(max_size)
    random.seed()
    start_at = min(int(samples.shape[0]*random.random()), samples.shape[0]-min_size-1)
    random.seed()
    segment_size = min(max(int((samples.shape[0]-start_at)*random.random()), min_size), max_size-1)
    end_at = min(start_at+segment_size+1, samples.shape[0])
    random.seed()
    if random.choice([True, False]):
        start_at, end_at = end_at, start_at
    speed = random.choice(speeds)
    return (start_at, end_at, speed)

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

def mix_it_up(audio_filenames, save_filename, min_time, max_time, segment_count, speeds, repeats):
    if max_time is None:
        max_time = min_time

    if not isinstance(audio_filenames, list):
        audio_filenames = [audio_filenames]

    audio_samples_list = []
    segment_ranges_list = []
    fps = None
    for audio_filename in audio_filenames:
        audio_clip = AudioFileClip(audio_filename)
        if fps is None:
            fps = audio_clip.fps
        audio_samples = audio_clip.to_soundarray(buffersize=1000)
        audio_samples_list.append(audio_samples)

        segment_ranges = []
        for i in range(segment_count):
            segment_range = get_random_segment(audio_samples,
                        audio_clip.fps*min_time, audio_clip.fps*max_time, speeds)
            segment_ranges.append(segment_range)
        segment_ranges_list.append(segment_ranges)

    built_samples = None
    for i in range(segment_count):
        for f in range(len(audio_samples_list)):
            start_at, end_at, speed = segment_ranges_list[f][i]
            if start_at>end_at:
                step = -1
            else:
                step = 1
            if speed>=1:
                selected_samples = audio_samples_list[f][start_at:end_at:step*speed, :]
                if speed>=1:
                    random.seed()
                    mult = random.choice(repeats)
                    selected_samples = numpy.concatenate([selected_samples]*mult, axis=0)
            else:
                selected_samples = audio_samples_list[f][start_at:end_at:step, :]
                selected_samples = numpy.repeat(selected_samples, int(1/speed), axis=0)
            if built_samples is None:
                built_samples = selected_samples
            else:
                built_samples = numpy.concatenate((built_samples, selected_samples), axis=0)
    del audio_samples_list

    new_audio_clip = SamplesAudioClip(built_samples, fps)
    new_audio_clip.save_as(save_filename)
    print "Final audio duration is ", new_audio_clip.duration, "sec"


mix_it_up(
    ["/home/sujoy/Videos/MusicVideos/Taio Cruz - Dynamite-Vysgv7qVYTo.mp4",],
    "/home/sujoy/Temporary/mixed.ogg",
    min_time=6,
    max_time=None,
    segment_count=10,
    repeats = [1,1,1, 2, 2, 3],
    speeds = [2]
)
