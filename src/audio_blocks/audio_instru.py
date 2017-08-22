import time
from xml.etree.ElementTree import Element as XmlElement

class AudioInstru(object):
    IdSeed = 0
    NameSeed = 0
    EPOCH_TIME = time.mktime(time.strptime("1 Jan 2017", "%d %b %Y"))
    TAG_NAME = "instru"

    @staticmethod
    def new_name():
        AudioInstru.NameSeed += 1
        elapsed_time = round(time.time()-AudioInstru.EPOCH_TIME, 3)
        return "{0}_{1}".format(elapsed_time, AudioInstru.NameSeed).replace(".", "")

    def __init__(self, name=None):
        if name is None:
            name = self.new_name()
        self.name = name
        self.id_num = AudioInstru.IdSeed
        AudioInstru.IdSeed += 1
        self.blocks = []

    def get_xml_element(self):
        elm = XmlElement(self.TAG_NAME)
        elm.attrib["name"] = "{0}".format(self.get_name())
        return elm

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def get_id(self):
        return self.id_num

    def __eq__(self, other):
        return isinstance(other, AudioInstru) and other.id_num == self.id_num

    def __hash__(self):
        return hash(("instru", self.id_num))

    def get_description(self):
        return self.name

    def add_block(self, block):
        self.blocks.append(block)

    def remove_block(self, block):
        if block in self.blocks:
            self.blocks.remove(block)

    def readjust_blocks(self):
        for block in self.blocks:
            block.readjust()

