import pyaudio
import Queue
import numpy
import threading
import time
from audio_group import AudioGroup
from audio_block import AudioBlock
import mido

class MidiThread(threading.Thread):
    def __init__(self):
        super(MidiThread, self).__init__()
        self.midi_queue = Queue.PriorityQueue()
        self.midi_output = mido.open_output(name="DAWpy", virtual=True)
        self.should_exit = False
        self.paused = False
        self.start()

    def run(self):
        item = None
        while not self.should_exit:
            if not self.paused:
                if item is None:
                    try:
                        item = self.midi_queue.get(block=False)
                    except Queue.Empty:
                        item = None
                if item:
                    if item[0]<=time.time():
                        self.midi_output.send(item[1])
                        item = None
            time.sleep(.1)

    def close(self):
        self.should_exit = True
        if self.is_alive():
            self.join()

class AudioServer(threading.Thread):
    PaManager = None
    Servers = []

    @staticmethod
    def get_default():
        if AudioServer.Servers:
            return AudioServer.Servers[0]
        return AudioServer()

    @staticmethod
    def close_all():
        while len(AudioServer.Servers)>0:
            server = AudioServer.Servers[0]
            server.close()
        del AudioServer.Servers[:]

    def __init__(self, buffer_mult=.95, host_api_name="jack"):
        super(AudioServer, self).__init__()
        self.midi_thread = MidiThread()
        self.pa_manager = pyaudio.PyAudio()

        self.output_device_index = None
        for i in xrange(self.pa_manager.get_host_api_count()):
            host_api_info = self.pa_manager.get_host_api_info_by_index(i)
            if host_api_info["name"].lower().find(host_api_name.lower()) == -1:
                continue
            for j in xrange(host_api_info["deviceCount"]):
                device_info = self.pa_manager.get_device_info_by_host_api_device_index(i, j)
                self.output_device_index = device_info["index"]

        self.audio_queue = Queue.Queue()
        self.audio_group = AudioGroup()
        self.should_exit = False
        self.paused = False
        self.buffer_mult = buffer_mult
        AudioServer.Servers.append(self)
        self.start()

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def add_block(self, block):
        self.audio_group.add_block(block)

    def remove_block(self, block):
        self.audio_group.remove_block(block)

    def run(self):
        self.stream = self.pa_manager.open(
                format=pyaudio.paFloat32,
                channels=AudioBlock.ChannelCount,
                rate= int(AudioBlock.SampleRate),
                output=True,
                frames_per_buffer = AudioBlock.FramesPerBuffer,
                stream_callback=self.stream_callback,
                output_device_index=self.output_device_index)
        self.stream.start_stream()
        self.audio_group.play()
        buffer_time = AudioBlock.FramesPerBuffer/float(AudioBlock.SampleRate)
        period = buffer_time*self.buffer_mult
        last_time = 0
        while not self.should_exit:
            if (time.time()-last_time)>period and not self.paused:
                audio_message = self.audio_group.get_samples(AudioBlock.FramesPerBuffer)
                if audio_message is not None:
                    self.audio_queue.put(audio_message, block=True)
            last_time = time.time()
            time.sleep(period)
        self.stream.stop_stream()
        self.stream.close()

    def stream_callback(self, in_data, frame_count, time_info, status):
        if self.paused:
            data = self.audio_group.blank_data.copy()
        else:
            try:
                audio_message = self.audio_queue.get(block=False)
                data = audio_message.samples
                if audio_message.midi_messages:
                    for midi_message in audio_message.midi_messages:
                        self.midi_thread.midi_queue.put((
                            time.time()+(midi_message.delay*1./AudioBlock.SampleRate),
                            midi_message.mido_message
                        ))
                if audio_message.block_positions:
                    for block, pos in audio_message.block_positions:
                        block.play_pos = pos

                self.audio_queue.task_done()
            except Queue.Empty:
                data = self.audio_group.blank_data.copy()
        return (data, pyaudio.paContinue)

    def close(self):
        self.midi_thread.close()
        self.should_exit = True
        if self.is_alive():
            self.join()
        AudioServer.Servers.remove(self)
        self.pa_manager.terminate()
