import threading, numpy, time, Queue
from audio_jack import AudioJack
from MotionPicture.audio_tools import AudioFFT
from MotionPicture.audio_tools import FreqBand
from MotionPicture.audio_tools import AudioRawSamples
from scipy import interpolate

class AudioPlayer(threading.Thread):
    def __init__(self, buffer_mult):
        threading.Thread.__init__(self)
        self.should_stop = False
        audio_jack = AudioJack.get_thread()

        if audio_jack:
            self.audio_queue = audio_jack.get_new_audio_queue()
            self.buffer_size = audio_jack.buffer_size*buffer_mult
            self.sample_rate = audio_jack.sample_rate

        self.period = audio_jack.period*.75
        self.audio_segments = []
        self.duration_size = 0
        self.t_size = 0.
        self.last_t = 0.
        self.buffer_time = self.buffer_size*1.0/self.sample_rate

        self.freq_bands = []
        self.audio_fft = None
        self.store_fft = False
        self.loop = True
        self.loop_start_at_size = 0

        self.segment_lock = threading.RLock()
        self.segment_add_queue = Queue.Queue()
        self.segment_remove_queue = Queue.Queue()
        self.segment_replace_queue = Queue.Queue()

        self.smoothing_size = 3

    def set_loop(self, value):
        self.loop = value

    def add_segment(self, segment, current_time_at=False):
        if current_time_at:
            segment.start_at_size = self.t_size
        self.segment_add_queue.put((segment, current_time_at))

    def remove_segment(self, segment):
        self.segment_lock.acquire()
        self.segment_remove_queue.put(segment)
        self.segment_lock.release()

    def replace_segment(self, old_segment, new_segment):
        self.segment_replace_queue.put((old_segment, new_segment))

    def remove_all_segments(self):
        self.segment_lock.acquire()
        for segment in self.audio_segments:
            self.segment_remove_queue.put(segment)
        self.segment_lock.release()

    def compute_duration(self):
        self.segment_lock.acquire()
        duration = 0
        max_start_at_size = 0
        for audio_segment in self.audio_segments:
            start_at_size = audio_segment.get_start_at_size()
            if max_start_at_size<start_at_size:
                max_start_at_size = start_at_size
            spread = start_at_size + audio_segment.get_duration_size()
            if spread>duration:
                duration = spread
        self.duration_size = duration
        if self.loop==2:
            self.loop_start_at_size = max_start_at_size
        self.segment_lock.release()

    def clear_queue(self):
        AudioJack.get_thread().clear_audio_queue(self.audio_queue)

    def reset_time(self):
        self.t = 0

    def handle_add_segment(self):
        if not self.segment_add_queue.empty():
            new_segment, current_time_at = self.segment_add_queue.get()
            if current_time_at:
                new_segment.start_at_size = self.t_size
            self.segment_lock.acquire()
            if new_segment not in self.audio_segments:
                self.audio_segments.append(new_segment)
            self.segment_lock.release()
            self.compute_duration()

    def run(self):
        blank_data = numpy.zeros((2, self.buffer_size), dtype="f")
        while not self.should_stop:
            full_buffer_size = self.buffer_size
            final_samples = None
            st = time.time()
            self.handle_add_segment()
            while not self.should_stop and \
                 (final_samples is None or \
                   final_samples.shape[1]<full_buffer_size) \
                                            and self.audio_segments:
                joined_samples = None
                buffer_size = min(self.buffer_size, self.duration_size-self.t_size)
                self.handle_add_segment()

                if not self.segment_remove_queue.empty():
                    old_segment = self.segment_remove_queue.get()
                    self.segment_lock.acquire()
                    if old_segment in self.audio_segments:
                        self.audio_segments.remove(old_segment)
                    self.segment_lock.release()
                    self.compute_duration()

                if not self.segment_replace_queue.empty():
                    old_segment, new_segment = self.segment_replace_queue.get()
                    start_at_size = audio_segment.get_start_at_size()
                    duration_size = audio_segment.get_duration_size()
                    if self.t_size+buffer_size<start_at_size or \
                       self.t_size>=start_at_size+duration_size:
                        middle_segment = None
                        new_segment.start_at_size = self.t_size
                    else:
                        current_time_size = self.t_size
                        old_samples = old_segment.get_samples_in_between_size(
                                    current_time_size, current_time_size+self.smoothing_size).copy()
                        new_samples = new_segment.get_samples_in_between_size(
                                    0, self.smoothing_size).copy()
                        middle_samples = numpy.concatenate((old_samples, new_samples), axis=1)
                        ts = numpy.arange(0, self.smoothing_size+middle_samples.shape[1])
                        xs = numpy.concatenate((ts[:old_samples.shape[1]], ts[-new_samples.shape[1]:]))
                        interpolator1 = interpolate.PchipInterpolator(xs, middle_samples[0, :])

                        middle_samples = interpolator1(ts)
                        middle_samples = numpy.vstack((middle_samples, middle_samples))
                        middle_segment = AudioRawSamples(middle_samples, self.sample_rate)
                        middle_segment.start_at_size = self.t_size
                        middle_segment.remove_after_end = True
                        new_segment.start_at_size = self.t_size + ts.shape[0]

                    self.segment_lock.acquire()
                    if old_segment in self.audio_segments:
                        self.audio_segments.remove(old_segment)
                    if middle_segment:
                        self.audio_segments.append(middle_segment)
                    if new_segment not in self.audio_segments:
                        self.audio_segments.append(new_segment)
                    self.segment_lock.release()
                    self.compute_duration()

                active_count = 0
                for s in range(len(self.audio_segments)):
                    audio_segment = self.audio_segments[s]
                    start_at_size = audio_segment.get_start_at_size()
                    duration_size = audio_segment.get_duration_size()
                    if self.t_size+buffer_size<start_at_size or \
                       self.t_size>=start_at_size+duration_size:
                        continue

                    active_count += 1

                    pre_blank_sample_count = start_at_size - self.t_size
                    post_blank_sample_count = self.t_size+buffer_size-start_at_size-duration_size

                    start_time_size = max(self.t_size-start_at_size, 0)
                    end_time_size = min(self.t_size+buffer_size-start_at_size, duration_size)
                    samples = audio_segment.get_samples_in_between_size(start_time_size, end_time_size).copy()
                    channels = samples.shape[0]
                    sample_count = samples.shape[1]

                    if pre_blank_sample_count>0:
                        pre_blank = numpy.zeros((channels, pre_blank_sample_count), dtype=numpy.float32)
                        samples = numpy.concatenate((pre_blank, samples), axis=1)

                    if post_blank_sample_count>0:
                        post_blank = numpy.zeros((channels, post_blank_sample_count), dtype=numpy.float32)
                        post_blank = post_blank.reshape(channels, -1).astype(numpy.float64)
                        samples = numpy.concatenate((samples, post_blank), axis=1)
                    samples = samples[:, :buffer_size]
                    if joined_samples is None:
                        joined_samples = samples
                    else:
                        joined_samples += samples
                if final_samples is None:
                    final_samples = joined_samples
                else:
                    try:
                        final_samples = numpy.concatenate((final_samples, joined_samples), axis=1)
                    except ValueError as e:
                        print e

                self.t_size += buffer_size

                while self.loop and self.t_size>=self.duration_size:
                    self.t_size -= (self.duration_size-self.loop_start_at_size)
                if active_count == 0:
                    final_samples = blank_data
                    break
            if final_samples is not None and final_samples.shape[1]>1:
                max_amp = numpy.amax(final_samples)
                #if max_amp>1.0:
                #    final_samples = final_samples/max_amp

                if self.freq_bands:
                    audio_fft = None
                    modified = False
                    for band in self.freq_bands:
                        if band.mult==1:
                            continue
                        if audio_fft is None:
                            audio_fft = AudioFFT(final_samples, self.sample_rate)
                        audio_fft.apply_freq_band(band)
                        modified = True

                    if modified:
                        final_samples = audio_fft.get_reconstructed_samples()
                    if self.store_fft:
                        self.audio_fft = audio_fft
                    audio_fft = None
                else:
                    if self.store_fft:
                        self.audio_fft = AudioFFT(final_samples, self.sample_rate)
                self.last_t_size = self.t_size
                try:
                    self.audio_queue.put(final_samples.astype(numpy.float32), block=False)
                except Queue.Full:
                    pass

            if self.loop == 2:
                s = 0
                self.segment_lock.acquire()
                while s<len(self.audio_segments):
                    audio_segment = self.audio_segments[s]
                    start_at_size = audio_segment.get_start_at_size()
                    duration_size = audio_segment.get_duration_size()
                    if self.t_size>start_at_size+duration_size:
                        if hasattr(audio_segment, "remove_after_end") and \
                            audio_segment.remove_after_end:
                            self.audio_segments.remove(audio_segment)
                            s -= 1
                    s += 1
                self.segment_lock.release()
                self.compute_duration()


            time.sleep(max(.01, self.period-(time.time()-st)))
        audio_jack = AudioJack.get_thread()
        if audio_jack:
            audio_jack.remove_audio_queue(self.audio_queue)
        self.audio_queue = None

    def close(self):
        self.should_stop = True
        if self.is_alive():
            self.join()
