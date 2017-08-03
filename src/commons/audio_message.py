class AudioMessage(object):
    def __init__(self, samples, midi_messages=None):
        self.samples = samples
        self.midi_messages = midi_messages
