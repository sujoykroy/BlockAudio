import time

class AudioInstru(object):
    IdSeed = 0
    NameSeed = 0
    EPOCH_TIME = time.mktime(time.strptime("1 Jan 2017", "%d %b %Y"))

    @staticmethod
    def new_name():
        AudioInstru.NameSeed += 1
        elapsed_time = round(time.time()-AudioInstru.EPOCH_TIME, 3)
        return "{0}_{1}".format(elapsed_time, AudioInstru.NameSeed).replace(".", "")

    def __init__(self, name=None):
        if name is None:
            name = self.new_name()
        self.name = name
        self.note_blocks = dict()
        self.id_num = AudioInstru.IdSeed
        AudioInstru.IdSeed += 1

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, AudioInstru) and other.id_num == self.id_num

    def __hash__(self):
        return self.id_num

