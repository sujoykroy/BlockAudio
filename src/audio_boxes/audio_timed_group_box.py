from audio_block_box import AudioBlockBox
from ..audio_blocks.audio_timed_group import AudioTimedGroup
from ..commons import draw_utils

class AudioTimedGroupBox(AudioBlockBox):
    def __init__(self, audio_block=None):
        self.block_boxes = []
        if not audio_block:
            should_populate = False
            audio_block = AudioTimedGroup()
        else:
            should_populate = True
        AudioBlockBox.__init__(self, audio_block)

        if should_populate:
            self.audio_block.lock.acquire()
            for block in self.audio_block.blocks:
                self.add_box(AudioBlockBox(block, parent_box=self))
            self.audio_block.lock.release()

    def add_block(self, block, at, y=0, sample_unit=True):
        if self.audio_block.add_block(block, at):
            block_box = AudioBlockBox(block, parent_box=self)
            self.add_box(block_box, y=y)

    def add_box(self, block_box, y=0):
        self.block_boxes.append(block_box)
        pos = self.audio_block.get_block_position(block_box.audio_block)
        block_box.set_x(pos*AudioBlockBox.PIXELS_PER_SAMPLE)
        block_box.set_y(y)
        self.update_size()

    def update_size(self):
        AudioBlockBox.update_size(self)
        height = 0
        for track_box in self.block_boxes:
            end_y = track_box.y + track_box.height
            if end_y>height:
                height = end_y
        self.height = height

    def draw(self, ctx):
        for block_box in self.block_boxes:
            block_box.draw(ctx)

