import threading, jack, numpy,Queue, time, tempfile, shutil
from MotionPicture.audio_tools.audio_file_writer  import *

class AudioJack(threading.Thread):
    _running_thread = None

    @staticmethod
    def get_thread():
        if AudioJack._running_thread is None:
            AudioJack._running_thread = AudioJack()
            AudioJack._running_thread.start()
        return AudioJack._running_thread

    @staticmethod
    def close_thread():
        if AudioJack._running_thread is None:
            return
        jack_thread = AudioJack._running_thread
        jack_thread.should_stop = True
        if jack_thread.is_alive():
            jack_thread.join()
        AudioJack._running_thread = None

    def __init__(self, name="jack"):
        threading.Thread.__init__(self)
        jack_name = "mpa_" + name
        self.should_stop = False
        self.started = False
        self.period = .01
        self.audio_queues = []
        self.queue_lock = threading.RLock()
        self.record = False
        self.output_record = False
        self.wave_file = None
        self.record_lock = threading.RLock()
        self.play_lock = threading.RLock()
        self.should_stop_playing_now = False

        try:
            jack.attach(jack_name)
            jack.activate()
        except jack.UsageError as e:
            pass
        except jack.NotConnectedError as e:
            self.should_stop = True
            self.buffer_size = 0
            self.sample_rate = 1.0
            return

        port_name = "out"
        jack.register_port(port_name+"_1", jack.IsOutput | jack.CanMonitor)
        jack.register_port(port_name+"_2", jack.IsOutput | jack.CanMonitor)
        jack.connect(jack_name+":"+port_name+"_1", "system:playback_1")
        jack.connect(jack_name+":"+port_name+"_2", "system:playback_2")

        port_name = "in"
        jack.register_port(port_name+"_1", jack.IsInput | jack.CanMonitor)
        jack.register_port(port_name+"_2", jack.IsInput | jack.CanMonitor)
        jack.connect("system:capture_1", jack_name+":"+port_name+"_1")
        jack.connect("system:capture_2", jack_name+":"+port_name+"_2")

        self.buffer_size = jack.get_buffer_size()
        self.sample_rate = jack.get_sample_rate()
        self.period = self.buffer_size*.5/self.sample_rate

        self.blank_data = numpy.zeros((2, self.buffer_size), dtype=numpy.float).astype('f')
        self.empty_data = numpy.zeros((2, self.buffer_size), dtype=numpy.float).astype('f')

        self.record_amplitude = 0

    def stop_playing_now(self):
        self.play_lock.acquire()
        self.should_stop_playing_now = True
        self.play_lock.release()

    def get_new_audio_queue(self):
        self.queue_lock.acquire()
        queue = Queue.Queue()
        self.audio_queues.append(queue)
        self.queue_lock.release()
        return queue

    def remove_audio_queue(self, queue):
        self.queue_lock.acquire()
        if queue in self.audio_queues:
            self.audio_queues.remove(queue)
        self.queue_lock.release()
        self.stop_playing_now()

    def clear_audio_queue(self, queue):
        self.queue_lock.acquire()
        try:
            while(queue.get(block=False) is not None):
                queue.task_done()
        except Queue.Empty as e:
            pass
        self.queue_lock.release()
        self.stop_playing_now()

    def clear_all_audio_queues(self):
        for queue in self.audio_queues:
            self.clear_audio_queue(queue)

    def set_record_file(self, filename):
        self.wave_file = WaveFileWriter(filename=filename, fileob=None, sample_rate=self.sample_rate)

    def save_record_file_as(self, filename):
        src_obj = self.wave_file.get_fileobject()
        if not src_obj:
            return False
        try:
            dest_obj = open(filename, "wb")
        except:
            return False
        self.record_lock.acquire()
        src_obj.seek(0)
        shutil.copyfileobj(src_obj, dest_obj)
        dest_obj.close()
        self.record_lock.release()
        return True

    def create_temp_record_file(self):
        self.record_lock.acquire()
        if self.wave_file:
            self.wave_file.close()
        fileob = tempfile.TemporaryFile(mode="w+b")
        self.wave_file = WaveFileWriter(filename=None, fileob=fileob, sample_rate=self.sample_rate)
        self.record_lock.release()

    def get_buffer_times(self):
        return numpy.arange(self.buffer_size)*1.0/self.sample_rate

    def run(self):
        leftover = None
        input_data = self.empty_data
        waiting_time = 0
        while not self.should_stop:
            output = None
            is_queue_output = False
            for audio_queue in self.audio_queues:
                self.queue_lock.acquire()
                try:
                    queue_output = audio_queue.get(block=False)
                    audio_queue.task_done()
                    is_queue_output = True
                except Queue.Empty as e:
                    #print "empty"
                    queue_output = None
                self.queue_lock.release()
                if queue_output is None:
                    continue
                if output is None:
                    output = queue_output
                    if self.record and self.wave_file and self.output_record and False:
                        self.record_lock.acquire()
                        self.wave_file.write(output)
                        self.record_lock.release()
                else:
                    span_diff = output.shape[1]-queue_output.shape[1]
                    #print "span_diff", span_diff
                    if span_diff<0:
                        zeros = numpy.zeros((output.shape[0], -span_diff), dtype="f")
                        output = numpy.concatenate((output, zeros), axis=1)
                    elif span_diff>0:
                        zeros = numpy.zeros((output.shape[0], span_diff), dtype="f")
                        queue_output = numpy.concatenate((queue_output, zeros), axis=1)
                    output += queue_output
                queue_output = None

            if output is None:
                if waiting_time<self.period:
                    waiting_time += .01
                    time.sleep(.01)
                    continue
                else:
                    waiting_time = 0
                    output = self.blank_data

            if leftover is not None:
                output = numpy.concatenate((leftover, output), axis=1)
            i = 0
            delay = 0
            st = time.time()
            should_exit = False
            while i<=output.shape[1]-self.buffer_size:
                self.play_lock.acquire()
                if self.should_stop_playing_now:
                    tail_count = min(output.shape[1]-self.buffer_size, self.buffer_size)
                    diedown_mask = numpy.repeat([numpy.linspace(1.0, 0, tail_count)], 2, axis=0)
                    diedown_mask.shape = (2, tail_count)
                    #output[:, i:i+tail_count] = (output[:, i:i+tail_count]*diedown_mask)
                    should_exit = True
                    self.should_stop_playing_now = False
                else:
                    should_exit = False
                self.play_lock.release()
                try:
                    output_data = output[:, i:i+self.buffer_size]
                    if self.record and self.wave_file:
                        if not self.output_record:
                            input_data = numpy.zeros((2, self.buffer_size), dtype=numpy.float).astype('f')
                    else:
                        if not self.output_record:
                            input_data = self.empty_data
                    jack.process(output_data, input_data)
                    if self.record and self.wave_file:
                        self.record_lock.acquire()
                        if not self.output_record:
                            self.wave_file.write(input_data)
                            pass
                        else:
                            self.wave_file.write(output_data)
                        self.record_lock.release()
                        self.record_amplitude = numpy.amax(input_data)
                    i += self.buffer_size

                except jack.InputSyncError:
                    pass
                except jack.OutputSyncError:
                    print "output sync error", time.time()
                    pass
                if should_exit:
                    break
            if not should_exit:
                if i<output.shape[1]:
                    leftover = output[:, i:]
                    #print "leftover", leftover.shape
                else:
                    leftover = None
            else:
                leftover = None
            #print "output.shape", output.shape
            delay = self.period-(time.time()-st)
            #print self.period
            if not is_queue_output:
                if delay<=self.period/10:
                    delay = self.period/2
                #print "delay", delay, self.period
                time.sleep(delay)

        jack.detach()
        self.record_lock.acquire()
        if self.wave_file:
            self.wave_file.close()
        self.wave_file = None
        self.record_lock.release()
        AudioJack._running_thread = None

    def close(self):
        self.should_stop = True
        if self.is_alive():
            self.join()
