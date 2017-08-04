class AudioMessage(object):
    def __init__(self, samples=None, midi_messages=None, block_positions=None):
        self.samples = samples
        if midi_messages is None:
            midi_messages = []
        self.midi_messages = midi_messages
        if block_positions is None:
            block_positions = []
        self.block_positions = block_positions
