import pyaudio
import Queue
import numpy
import threading
import time
from audio_track import AudioTrack

class AudioMasterTrack(AudioTrack):
    def __init__(self):
        super(AudioMasterTrack, self).__init__()
        self.sub_tracks = []

        self.lock = threading.RLock()
        self.blank_data = self.get_blank_data(AudioTrack.FramesPerBuffer)

    def add_track(self, track):
        self.lock.acquire()
        self.sub_tracks.append(track)
        self.lock.release()
        track.play()

    def remove_track(self, track):
        self.lock.acquire()
        if track in self.sub_tracks:
            self.sub_tracks.remove(track)
        self.lock.release.acquire()

    def get_samples(self, frame_count):
        if self.paused:
            return self.blank_data.copy()

        self.lock.acquire()
        sub_track_count = len(self.sub_tracks)
        self.lock.release()

        self._samples = None
        for i in xrange(sub_track_count):

            self.lock.acquire()
            if i <len(self.sub_tracks):
                sub_track = self.sub_tracks[i]
            else:
                sub_track = None
            self.lock.release()

            if not sub_track:
                break

            sub_track_samples = sub_track.get_samples(frame_count)
            if sub_track_samples is None:
                continue

            """
            if sub_track_samples.shape[0]<frame_count:#this is redundant, needs to be thrown out
                blank_data = self.blank_data[:frame_count-sub_track_samples.shape[0], :]
                sub_track_samples = numpy.append(sub_track_samples, blank_data, axis=0)
            """

            if self._samples is None:
                self._samples = sub_track_samples.copy()
            else:
                self._samples = self._samples + sub_track_samples

        if  self._samples is None:
            self._samples = self.blank_data.copy()
        return self._samples

class AudioTimedMasterTrack(AudioTrack):
    def __init__(self):
        super(AudioTimedMasterTrack, self).__init__()
        self.sub_tracks = []
        self.sub_tracks_positions = []

        self.lock = threading.RLock()
        self.blank_data = self.get_blank_data(AudioTrack.FramesPerBuffer)

    def add_sub_track(self, track, at, stretch=True):
        self.lock.acquire()
        at *= int(at*AudioTrack.SampleRate)
        if track not in self.sub_tracks:
            self.sub_tracks.append(track)
            self.sub_tracks_positions.append(at)
        else:
            self.sub_tracks_positions[self.sub_tracks.index(track)]=(at)
        self.lock.release()
        if stretch:
            self.calculate_duration()

    def remove_sub_track(self, track, stretch=True):
        self.lock.acquire()
        if track in self.sub_tracks:
            index = self.sub_tracks.index(track)
            del self.sub_tracks[index]
            del self.sub_tracks_positions[index]
        self.lock.release()
        if stretch:
            self.calculate_duration()

    def calculate_duration(self):
        self.lock.acquire()
        sub_track_count = len(self.sub_tracks)
        self.lock.release()

        duration = 0
        for i in xrange(sub_track_count):
            if i<len(self.sub_tracks):
                sub_track = self.sub_tracks[i]
                sub_track_start_pos = self.sub_tracks_positions[i]
            else:
                sub_track = None
            self.lock.release()

            if not sub_track:
                break

            end_at = self.sub_tracks_postion[i]+sub_track.calculate_duration()
            if end_at>duration:
                duration = end_at
        self.duration = duration
        return duration

    def get_samples(self, frame_count, start_from=None, use_loop=True):
        if self.paused:
            return self.blank_data

        self.lock.acquire()
        sub_track_count = len(self.sub_tracks)
        self.lock.release()
        if start_from is None:
            start_pos = self.current_pos
        else:
            start_pos = start_from

        if self.loop and use_loop:
            data = None

            while data is None or data.shape[0]<frame_count:
                sub_frame_count = min(self.duration-start_pos, frame_count)
                seg = self.get_samples(sub_frame_count, start_from=start_pos, use_loop=False)
                if data is None:
                    data = seg
                else:
                    data = numpy.append(data, seg, axis=0)
                start_pos += seg.shape[0]
                start_pos %= self.duration

            if start_from is None:
                self.current_pos = start_pos
            return data

        samples = None
        for i in xrange(sub_track_count):
            sub_track_samples = None
            self.lock.acquire()
            if i<len(self.sub_tracks):
                sub_track = self.sub_tracks[i]
                sub_track_start_pos = self.sub_tracks_positions[i]
            else:
                sub_track = None
            self.lock.release()

            if not sub_track:
                break
            if start_pos+frame_count<sub_track_start_pos:
                continue

            if sub_track.loop:
                if sub_track_start_pos<start_pos:
                    elapsed = start_pos-sub_track_start_pos
                    sub_track_start_pos += (elapsed//sub_track.duration)*sub_track.duration
            elif sub_track_start_pos+sub_track.duration<start_pos:
                continue

            if sub_track_start_pos>start_pos:
                sub_track_samples = self.blank_data[:sub_track_start_pos-start_pos, :]
                sub_track_start_from = 0
                sub_frame_count = start_pos + frame_count-sub_track_start_pos
            else:
                sub_track_samples = None
                sub_track_start_from = start_pos-sub_track_start_pos
                sub_frame_count = frame_count

            seg = sub_track.get_samples(sub_frame_count, start_from=sub_track_start_from)
            if sub_track_samples is None:
                sub_track_samples = seg
            else:
                sub_track_samples = numpy.append(sub_track_samples, seg, axis=0)

            if samples is None:
                samples = sub_track_samples
            else:
                samples  = samples + sub_track_samples

        if  samples is None:
            samples = self.blank_data[:frame_count, :]

        if start_from is None:
            self.current_pos = start_pos + frame_count
            if self.current_pos>self.duration:
                self.current_pos = self.duration

        return samples

class AudioServer(threading.Thread):
    PaManager = None

    def __init__(self, sample_rate=44100):
        super(AudioServer, self).__init__()
        self.pa_manager = pyaudio.PyAudio()

        AudioTrack.FramesPerBuffer = 1024
        AudioTrack.ChannelCount = 2
        AudioTrack.SampleRate = sample_rate

        self.audio_queue = Queue.Queue()
        self.master_track = AudioMasterTrack()
        self.should_exit = False
        self.start()

    def run(self):
        self.stream = self.pa_manager.open(
                format=pyaudio.paFloat32,
                channels=AudioTrack.ChannelCount,
                rate= AudioTrack.SampleRate,
                output=True,
                frames_per_buffer = AudioTrack.FramesPerBuffer,
                stream_callback=self.stream_callback)
        self.stream.start_stream()
        self.master_track.play()
        buffer_time = AudioTrack.FramesPerBuffer/float(AudioTrack.SampleRate)
        period = buffer_time*.5
        last_time = 0
        while not self.should_exit:
            if (time.time()-last_time)>period:
                samples = self.master_track.get_samples(AudioTrack.FramesPerBuffer)
                self.audio_queue.put(samples, block=True)
            last_time = time.time()
            time.sleep(period)
        self.stream.stop_stream()
        self.stream.close()

    def stream_callback(self, in_data, frame_count, time_info, status):
        try:
            data = self.audio_queue.get(block=False)
            self.audio_queue.task_done()
        except Queue.Empty:
            data = self.master_track.blank_data.copy()
        return (data, pyaudio.paContinue)

    def close(self):
        self.should_exit = True
        if self.is_alive():
            self.join()
        self.pa_manager.terminate()
