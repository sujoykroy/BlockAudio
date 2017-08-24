from gi.repository import Gtk, Gdk
from ..commons import KeyboardState, MusicNote, Color, draw_utils
from ..audio_blocks import AudioServer, AudioKeypadGroup, AudioTimedGroup
from ..audio_blocks import AudioFormulaInstru, AudioFileInstru
from .. import formulators
import multiprocessing
import Queue
import time

from gi.repository import GObject
GObject.threads_init()

class PianoKey(object):
    FillColor = Color.parse("431234")
    PressedColor = Color.parse("431266")
    BorderColor = Color.parse("000000")
    KeyNameColor = Color.parse("FFFFFF")
    NoteColor = Color.parse("ed4a4a")

    def __init__(self, key_name):
        self.left = 0
        self.top = 0
        self.width = 1
        self.height = 1
        self.key_name = key_name
        self.note = None

    def is_within(self, point):
        return self.left<=point.x<=self.top and self.top<=point.y<=self.bottom

    def draw_path(self, ctx):
        ctx.new_path()
        ctx.move_to(self.left, self.top)
        ctx.line_to(self.left+self.width, self.top)
        ctx.line_to(self.left+self.width, self.top+self.height)
        ctx.line_to(self.left, self.top+self.height)
        ctx.close_path()

class PianoBoard(object):
    def __init__(self, key_names):
        self.piano_keys = dict()
        self.scale_incre = 0

        piano_key_lines = []
        max_piano_key_line_count = 0

        for key_line in key_names.strip().split("\n"):
            if not key_line:
                continue
            keys = key_line.strip().split(" ")
            piano_key_line = []

            for key in keys:
                if not key:
                    continue
                piano_key = PianoKey(key)
                piano_key_line.append(piano_key)
                self.piano_keys[piano_key.key_name] = piano_key
            if not piano_key_line:
                continue

            piano_key_lines.append(piano_key_line)
            if len(piano_key_line)>max_piano_key_line_count:
                max_piano_key_line_count = len(piano_key_line)

        key_width = 1./(max_piano_key_line_count+2)
        key_height = 1./len(piano_key_lines)

        for r in xrange(len(piano_key_lines)):
            piano_key_line = piano_key_lines[r]
            offset_x = (1-key_width*len(piano_key_line))*.5
            for c in xrange(len(piano_key_line)):
                piano_key = piano_key_line[c]
                piano_key.left = offset_x + c*key_width
                piano_key.top = key_height*r
                piano_key.width = key_width
                piano_key.height = key_height

        self.scale_incre = 0
        self.key_maps = dict()

    def set_maps(self, keys, start_note):
        keys = keys.split(" ")
        note = MusicNote.get_note(start_note)
        for key in keys:
            piano_key = self.piano_keys.get(key)
            if piano_key:
                piano_key.note = note
            note = note.get_next_note()
            if note is None:
                break

    def get_note_name(self, piano_key):
        if not piano_key.note:
            return ""
        note = piano_key.note.get_next_note(self.scale_incre*12)
        if note:
            return note.name
        return ""

    @classmethod
    def create_english_keyboard(cls):
        key_names = """
        1 2 3 4 5 6 7 8 9 0 - =
        q w e r t y u i o p [ ] \\
        a s d f g h j k l ; '
        z x c v b n m , . /
        """
        board = cls(key_names)
        board.set_maps("z s x d c v g b h n j m , l . ; /", "C4")
        board.set_maps("q 2 w 3 e r 5 t 6 y 7 u i 9 o 0 p [ = ] \\", "C5")
        return board

class KeypadServerProcess(multiprocessing.Process):
    def __init__(self, queue):
        super(KeypadServerProcess, self).__init__()
        self.queue = queue
        self.should_exit = multiprocessing.Value('i', 0)
        self.start()

    def run(self):
        self.audio_server = AudioServer(buffer_mult=1)
        self.audio_server.play()

        self.audio_keypad_group = AudioKeypadGroup()
        self.audio_server.add_block(self.audio_keypad_group)
        self.audio_samples_instru = None

        formula_instru = AudioFormulaInstru(formulators.TomTomFormulator())
        self.audio_samples_instru = formula_instru

        self.active_blocks = dict()

        while not self.should_exit.value:
            try:
                data = self.queue.get(block=False)
            except Queue.Empty:
                data = None
            if data:
                key, note_name = data[:]
                if note_name:
                    note_block = self.audio_samples_instru.create_note_block(note_name)
                    audio_block = self.audio_keypad_group.add_samples(note_block.samples)
                    self.active_blocks[key] = audio_block
                elif key in self.active_blocks:
                    self.active_blocks[key].end_smooth()
                    del self.active_blocks[key]
            time.sleep(.01)
        self.audio_server.close()

    def close(self):
        with self.should_exit.get_lock():
            self.should_exit.value += 1
        self.join()

class PianoKeypad(Gtk.Window):
    def __init__(self, width=800, height=300, use_server_process=not True, owner=None):
        Gtk.Window.__init__(self, title="Piano Keypad", resizable=True)
        self.set_size_request(width, height)
        self.keyboard_state = KeyboardState()

        self.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|\
            Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)

        self.connect("delete-event", self.quit)
        self.set_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)

        self.instru_name_label = Gtk.Label()
        self.scale_incre_spin_button = Gtk.SpinButton()
        self.scale_incre_spin_button.set_range(-6, 5)
        self.scale_incre_spin_button.set_increments(1, 1)
        self.scale_incre_spin_button.connect(
            "value-changed",
            self.scale_incre_spin_button_value_changed)

        self.record_button = Gtk.ToggleButton("Record")
        self.record_button.connect("toggled", self.record_button_toggled)

        self.piano_board_area = Gtk.DrawingArea()
        self.piano_board_area.connect("draw", self.on_piano_board_draw)

        self.piano_board = PianoBoard.create_english_keyboard()

        self.owner = owner
        self.pressed_keys = dict()
        self.use_server_process = use_server_process

        self.audio_server = None
        self.server_process = None

        if not self.use_server_process:
            self.audio_keypad_group = AudioKeypadGroup()

            #self.audio_server = AudioServer.get_default()#AudioServer(buffer_mult=.98)
            #self.audio_server.add_block(self.audio_keypad_group)
            self.audio_samples_instru = None
        else:
            self.server_process_queue = multiprocessing.Queue()
            self.server_process = KeypadServerProcess(self.server_process_queue)

        self.info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.info_box.pack_start(
            Gtk.Label("Instrument: "), expand=False, fill=False, padding=5)
        self.info_box.pack_start(
            self.instru_name_label, expand=False, fill=False, padding=5)
        self.info_box.pack_start(
            self.record_button, expand=False, fill=False, padding=5)
        self.info_box.pack_end(
            self.scale_incre_spin_button, expand=False, fill=False, padding=5)
        self.info_box.pack_end(
            Gtk.Label("Scale Increment"), expand=False, fill=False, padding=5)

        self.root_box = Gtk.VBox()
        self.add(self.root_box)
        self.root_box.pack_end(self.piano_board_area, expand=True, fill=True, padding=0)
        self.root_box.pack_start(self.info_box, expand=False, fill=False, padding=0)
        self.root_box.pack_start(Gtk.HSeparator(), expand=False, fill=False, padding=0)
        self.show_all()

    def set_instru(self, instru):
        self.audio_samples_instru = instru
        self.instru_name_label.set_markup("<b>"+instru.get_name() + "</b>")

    def scale_incre_spin_button_value_changed(self, widget):
        self.piano_board.scale_incre = widget.get_value()
        self.piano_board_area.queue_draw()

    def record_button_toggled(self, widget):
        recorded_values = self.audio_keypad_group.set_record(widget.get_active())
        if not recorded_values:
            return
        end_time = time.time()
        min_start_time = end_time
        for i in xrange(len(recorded_values)):
            note_name, start_time, end_time = recorded_values[i][:]
            if end_time is None:
                end_time = start_time + 1
            recorded_values[i][2] = end_time-start_time
            if min_start_time>start_time:
                min_start_time = start_time

        timed_group = AudioTimedGroup()
        for i in xrange(len(recorded_values)):
            note_name, start_time, duration = recorded_values[i][:]
            start_time -= min_start_time
            block = self.audio_samples_instru.create_note_block(note_name)
            timed_group.add_block(block, start_time, "sec", self.owner.beat)
            block.start_time.set_unit("beat", self.owner.beat)
        timed_group.set_name("rec_{0}".format(time.time()))
        timed_group.set_duration_unit("sec", self.owner.beat)
        timed_group.set_duration_value(end_time-min_start_time, self.owner.beat)
        timed_group.set_duration_unit("beat", self.owner.beat)
        self.owner.append_timed_group(timed_group)

    def on_key_press(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=True)
        if event.string not in self.pressed_keys:
            self.pressed_keys[event.string] = None
            piano_key = self.piano_board.piano_keys.get(event.string)
            if not self.use_server_process:
                if piano_key and self.audio_samples_instru and piano_key.note:
                    note_name = self.piano_board.get_note_name(piano_key)
                    note_block = \
                        self.audio_samples_instru.create_note_block(note_name)
                    audio_block = self.audio_keypad_group.add_samples(
                            note_block.samples, note_name)
                    self.pressed_keys[event.string] = audio_block
            else:
                if piano_key and piano_key.note:
                    self.server_process_queue.put((event.string, piano_key.note.name))
            self.piano_board_area.queue_draw()

    def on_key_release(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=False)
        if event.string in self.pressed_keys:
            if not self.use_server_process:
                audio_block = self.pressed_keys[event.string]
                if audio_block:
                    audio_block.end_smooth()
            else:
                self.server_process_queue.put((event.string, ''))
            del self.pressed_keys[event.string]
            self.piano_board_area.queue_draw()

    def on_piano_board_draw(self, widget, ctx):
        padding = 5
        ww = widget.get_allocated_width()-2*padding
        wh = widget.get_allocated_height()-2*padding
        ctx.translate(padding, padding)

        for piano_key in self.piano_board.piano_keys.values():
            ctx.save()
            ctx.scale(ww, wh)
            piano_key.draw_path(ctx)
            ctx.restore()
            if piano_key.key_name in self.pressed_keys:
                draw_utils.draw_fill(ctx, PianoKey.PressedColor)
            else:
                draw_utils.draw_fill(ctx, PianoKey.FillColor)

            ctx.save()
            ctx.scale(ww, wh)
            piano_key.draw_path(ctx)
            ctx.restore()
            draw_utils.draw_stroke(ctx, 2, PianoKey.BorderColor)

            ctx.save()
            ctx.translate(ww*(piano_key.left+piano_key.width*.5),
                          wh*(piano_key.top+piano_key.height)-5)
            draw_utils.draw_text(ctx, piano_key.key_name,
                        x=0, y=0, width=piano_key.width*ww,
                        align="bottom-hcenter", text_color=PianoKey.KeyNameColor)
            ctx.restore()

            ctx.save()
            ctx.translate(ww*(piano_key.left+piano_key.width*.5),
                          wh*(piano_key.top)+5)
            draw_utils.draw_text(
                        ctx, self.piano_board.get_note_name(piano_key),
                        x=0, y=0, width=piano_key.width*ww*.25, fit_width=True,
                        align="hcenter", text_color=PianoKey.NoteColor)
            ctx.restore()

    def quit(self, wiget, event):
        if not self.use_server_process:
            self.audio_server.remove_block(self.audio_keypad_group)
        else:
            if self.server_process:
                self.server_process.close()
