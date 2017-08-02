from audio_block_box import AudioBlockBox
from ..audio_blocks.audio_timed_group import AudioTimedGroup
from ..commons import draw_utils

class AudioTimedGroupBox(AudioBlockBox):
    def __init__(self, audio_block=None):
        self.block_boxes = dict()
        self.block_zs = []
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
        self.block_boxes[block_box.get_id()] = block_box
        self.update_box_position(block_box, y)
        self.block_zs.append(block_box.get_id())
        self.update_size()

    def update_box_position(self, block_box, y):
        pos = self.audio_block.get_block_position(block_box.audio_block)
        block_box.set_x(pos*AudioBlockBox.PIXELS_PER_SAMPLE)
        block_box.set_y(y)

    def update_size(self):
        AudioBlockBox.update_size(self)
        height = 0
        for track_box in self.block_boxes.values():
            end_y = track_box.y + track_box.height
            if end_y>height:
                height = end_y
        self.height = height

    def draw(self, ctx):
        for block_box_id in self.block_zs:
            self.block_boxes.get(block_box_id).draw(ctx)

    def find_box_at(self, point):
        point = self.transform_point(point)
        for block_box_id in reversed(self.block_zs):
            block_box = self.block_boxes.get(block_box_id)
            if block_box.is_within(point):
                return block_box
        return None

    def move_box(self, block_box, init_position, start_point, end_point):
        start_point = self.transform_point(start_point)
        end_point = self.transform_point(end_point)
        xdiff = end_point.x - start_point.x
        ydiff = end_point.y - start_point.y

        sample_pos = (init_position.x+xdiff)*1.0/AudioBlockBox.PIXELS_PER_SAMPLE
        self.audio_block.set_block_at(block_box.audio_block, int(sample_pos))

        self.update_box_position(block_box, init_position.y+ydiff)
        self.update_size()
