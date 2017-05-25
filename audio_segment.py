import threading

class AudioSegment(object):
    IdSeed = 0
    CreationLock = threading.RLock()

    def __init__(self, start_at, duration):
        self.start_at = start_at
        self.duration = duration
        self.loop = False
        AudioSegment.CreationLock.acquire()
        self.id_num = AudioSegment.IdSeed
        AudioSegment.IdSeed += 1
        AudioSegment.CreationLock.release()

    def __eq__(self, other):
        return isinstance(other, AudioSegment) and other.id_num == self.id_num

    def set_loop(self, bool_value):
        self.loop = bool_value

    def get_start_at(self):
        return self.start_at

    def get_duration(self):
        return self.duration
