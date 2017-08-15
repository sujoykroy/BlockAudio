from audio_block_box import AudioBlockBox
from ..audio_blocks.audio_timed_group import AudioTimedGroup
from ..commons import draw_utils
from expander_box import ExpanderBox

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
        if not sample_unit:
            at = at*1./AudioBlockBox.PIXEL_PER_SAMPLE
        if self.audio_block.add_block(block, at, sample_unit=True):
            block_box = AudioBlockBox(block, parent_box=self)
            self.add_box(block_box, y=y)

    def add_box(self, block_box, y=0):
        self.block_boxes[block_box.get_id()] = block_box
        self.update_box_position(block_box, y)
        self.block_zs.append(block_box.get_id())
        self.update_size()

    def update_box_position(self, block_box, y=None):
        pos = self.audio_block.get_block_position(block_box.audio_block)
        block_box.set_x(pos*AudioBlockBox.PIXEL_PER_SAMPLE)
        if y is not None:
            block_box.set_y(y)

    def update_size(self):
        AudioBlockBox.update_size(self)
        height = 0
        for track_box in self.block_boxes.values():
            end_y = track_box.y + track_box.height
            if end_y>height:
                height = end_y
        self.height = height

    def draw(self, ctx, visible_area=None, selected_box=None):
        for block_box_id in self.block_zs:
            box = self.block_boxes.get(block_box_id)
            if visible_area and \
                (box.x+box.scale_x*box.width<visible_area.left or \
                 box.x>visible_area.left+visible_area.width):
                continue
            box.draw(ctx, is_selected=(selected_box==box))

    def find_box_at(self, point):
        rel_point = self.transform_point(point)
        for block_box_id in reversed(self.block_zs):
            block_box = self.block_boxes.get(block_box_id)
            if block_box.is_within(rel_point):
                tail_box = block_box.get_tail_box(abs_at=point)
                if tail_box:
                    return tail_box
                return block_box
        return None

    def move_box(self, box, init_position, start_point, end_point, beat):
        start_point = self.transform_point(start_point)
        end_point = self.transform_point(end_point)
        xdiff = end_point.x - start_point.x
        ydiff = end_point.y - start_point.y
        if isinstance(box, AudioBlockBox):
            xpos = init_position.x+xdiff
            if beat:
                sample_pos = beat.pixel2sample(xpos)
            else:
                sample_pos = xpos*1.0/AudioBlockBox.PIXEL_PER_SAMPLE
            if sample_pos<0:
                sample_pos = 0

            self.audio_block.set_block_position(box.audio_block, int(sample_pos), beat)
            self.update_box_position(box, init_position.y+ydiff)

        elif box.parent_box and box.parent_box.tail_box and box == box.parent_box.tail_box :
            xpos = end_point.x
            if beat:
                sample_pos = beat.pixel2sample(xpos)
            else:
                sample_pos = xpos*1.0/AudioBlockBox.PIXEL_PER_SAMPLE

            self.audio_block.stretch_block_to(box.parent_box.audio_block, int(sample_pos), beat)
            box.parent_box.update_size()
            self.update_box_position(box.parent_box, box.parent_box.y)
        self.update_size()

