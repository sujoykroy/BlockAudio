from gi.repository import Gtk, Gdk
from ..audio_boxes import *
from ..audio_blocks import *
from ..formulators import *
from ..commons import Point, Beat, KeyboardState, Rect
from ..commons import MusicNote
from .. import gui_utils
from timed_group_page import TimedGroupPage

from gi.repository import GObject
GObject.threads_init()

class AudioSequencer(Gtk.Window):
    def __init__(self, width=800, height=600,
                instru_list=None, timed_group_list=None, file_block_list=None):
        Gtk.Window.__init__(self, title="Sequencer", resizable=True)
        self.set_size_request(width, height)

        self.opened_audio_blocks = dict()
        self.beat = Beat(bpm=120/8,
                         sample_rate=AudioBlock.SampleRate,
                         pixel_per_sample=AudioBlockBox.PIXEL_PER_SAMPLE)
        self.tge_rect = Rect(0, 0, 1, 1)
        self.keyboard_state = KeyboardState()

        self.connect("delete-event", self.quit)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)

        if not instru_list:
            instru_list = []
        if not file_block_list:
            file_block_list = []
        if not timed_group_list:
            timed_group = AudioTimedGroup()
            timed_group.set_name("Main")
            timed_group_list = [timed_group]

        self.instru_list = instru_list
        self.timed_group_list = timed_group_list
        self.file_block_list = file_block_list

        self.instru_list_label = Gtk.Label("Instruments")
        self.instru_list_label.set_pattern("___________")
        self.instru_list_label.set_justify(Gtk.Justification.CENTER)

        self.instru_list_view = Gtk.TreeView()
        self.instru_list_view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0))
        self.instru_list_view.set_headers_visible(False)

        self.add_file_instru_button = Gtk.Button("Add File Instrument")
        self.add_file_instru_button.connect("clicked", self.add_file_instru_button_clicked)

        self.formula_list_label = Gtk.Label("Formulators")
        self.formula_list_label.set_pattern("___________")
        self.formula_combo_box = gui_utils.NameValueComboBox()
        self.formula_combo_box.build_and_set_model([
            ["Sine", SineFormulator]
        ])
        self.add_formula_instru_button = Gtk.Button("Add Formula Instrument")
        self.add_formula_instru_button.connect("clicked", self.add_formula_instru_button_clicked)

        self.timed_group_list_label = Gtk.Label("Block Groups")
        self.timed_group_list_label.set_pattern("____________")
        self.timed_group_list_label.set_justify(Gtk.Justification.CENTER)

        self.timed_group_list_view = Gtk.TreeView()
        self.timed_group_list_view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0))
        self.timed_group_list_view.set_headers_visible(False)
        self.timed_group_list_view.connect(
            "row-activated", self.timed_group_list_view_row_activated)

        self.add_block_group_button = Gtk.Button("Add Block Group")
        self.add_block_group_button.connect("clicked", self.add_block_group_button_clicked)

        self.file_block_list_label = Gtk.Label("File Blocks")
        self.file_block_list_label.set_pattern("____________")
        self.file_block_list_label.set_justify(Gtk.Justification.CENTER)

        self.file_block_list_view = Gtk.TreeView()
        self.file_block_list_view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0))
        self.file_block_list_view.set_headers_visible(False)

        self.add_file_block_button = Gtk.Button("Add File Block")
        self.add_file_block_button.connect("clicked", self.add_file_block_button_clicked)

        self.root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.root_box)

        self.blockinstru_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.blockinstru_box.set_size_request(100, -1)

        #instru list display
        self.blockinstru_box.pack_start(
                self.instru_list_label, expand=False, fill=False, padding=5)
        self.instru_list_view_container = Gtk.ScrolledWindow()
        self.instru_list_view_container.add_with_viewport(self.instru_list_view)
        self.blockinstru_box.pack_start(
                self.instru_list_view_container, expand=True, fill=True, padding=0)

        self.blockinstru_box.pack_start(
                self.add_file_instru_button, expand=False, fill=False, padding=5)

        self.blockinstru_box.pack_start(
                self.formula_list_label, expand=False, fill=False, padding=5)
        self.blockinstru_box.pack_start(
                self.formula_combo_box, expand=False, fill=False, padding=0)
        self.blockinstru_box.pack_start(
                self.add_formula_instru_button, expand=False, fill=False, padding=5)

        #block group list display
        self.blockinstru_box.pack_start(
                self.timed_group_list_label, expand=False, fill=False, padding=5)
        self.timed_group_list_view_container = Gtk.ScrolledWindow()
        self.timed_group_list_view_container.add_with_viewport(self.timed_group_list_view)
        self.blockinstru_box.pack_start(
                self.timed_group_list_view_container, expand=True, fill=True, padding=5)
        self.blockinstru_box.pack_start(
                self.add_block_group_button, expand=False, fill=False, padding=0)

        #file block list display
        self.blockinstru_box.pack_start(
                self.file_block_list_label, expand=False, fill=False, padding=5)
        self.file_block_list_view_container = Gtk.ScrolledWindow()
        self.file_block_list_view_container.add_with_viewport(self.file_block_list_view)
        self.blockinstru_box.pack_start(
                self.file_block_list_view_container, expand=True, fill=True, padding=5)
        self.blockinstru_box.pack_end(
                self.add_file_block_button, expand=False, fill=False, padding=0)

        self.block_instru_notebook = Gtk.Notebook()
        self.block_instru_notebook.set_scrollable(True)

        self.root_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.root_paned.add1(self.blockinstru_box)
        self.root_paned.add2(self.block_instru_notebook)

        self.root_box.pack_start(self.root_paned, expand=True, fill=True, padding=5)

        self.build_instru_list_view()
        self.build_timed_group_list_view()
        self.build_file_block_list_view()

        self.show_all()
        self.load_block(self.timed_group_list[0])

    def add_page(self, page, name):
        if isinstance(page, TimedGroupPage):
            if page.audio_block.get_id() in self.opened_audio_blocks:
                return
            self.opened_audio_blocks[page.audio_block.get_id()] = page

        page.init_show()
        widget = page.get_widget()

        close_button = Gtk.Button()
        close_button.set_image(Gtk.Image.new_from_icon_name("edit_-delete", Gtk.IconSize.BUTTON))
        close_button.connect("clicked", self.notebook_tab_close_button_clicked, page)

        tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        tab_label.pack_start(Gtk.Label(name), expand=True, fill=True, padding=0)
        tab_label.pack_start(close_button, expand=False, fill=False, padding=0)
        tab_label.show_all()

        self.block_instru_notebook.append_page(widget, tab_label)
        self.block_instru_notebook.show()

    def notebook_tab_close_button_clicked(self, widget, page):
        self.block_instru_notebook.remove(page.get_widget())

        if isinstance(page, TimedGroupPage):
            if page.audio_block.get_id() in self.opened_audio_blocks:
                del self.opened_audio_blocks[page.audio_block.get_id()]

    def load_block(self, audio_block):
        self.add_page(
            TimedGroupPage(self, audio_block),
            audio_block.get_name()
        )

    def add_file_instru_button_clicked(self, widget):
        filename = gui_utils.FileOp.choose_file(self, "open", "audio")
        if filename:
            instru = AudioFileInstru(filename=filename)
            self.instru_list.append(instru)
            self.build_instru_list_view()

    def add_formula_instru_button_clicked(self, widget):
        formulator_class = self.formula_combo_box.get_value()
        if formulator_class:
            instru = AudioFormulaInstru(formulator=formulator_class())
            self.instru_list.append(instru)
            self.build_instru_list_view()

    def add_block_group_button_clicked(self, widget):
        timed_group = AudioTimedGroup()
        self.timed_group_list.append(timed_group)
        self.build_timed_group_list_view()

    def add_file_block_button_clicked(self, widget):
        filename = gui_utils.FileOp.choose_file(self, "open", "audio")
        if filename:
            block = AudioFileBlock(filename)
            self.file_block_list.append(block)
            self.build_file_block_list_view()

    def timed_group_list_view_row_activated(self, tree_view, path, column):
        treeiter = tree_view.get_model().get_iter(path)
        if not treeiter:
            return
        block = tree_view.get_model().get_value(treeiter, 1)
        self.load_block(block)

    def build_instru_list_view(self):
        instru_store = Gtk.TreeStore(str, object)

        instru_dict = dict()
        for instru in self.instru_list:
            instru_dict[instru.get_name()] = instru
        for name in sorted(instru_dict.keys()):
            instru_store.append(None, [name, instru_dict[name]])
        self.instru_list_view.set_model(instru_store)

    def build_timed_group_list_view(self):
        group_store = Gtk.TreeStore(str, object)

        group_dict = dict()
        for group in self.timed_group_list:
            group_dict[group.get_name()] = group
        for name in sorted(group_dict.keys()):
            group_store.append(None, [name, group_dict[name]])
        self.timed_group_list_view.set_model(group_store)

    def build_file_block_list_view(self):
        file_block_store = Gtk.TreeStore(str, object)

        file_block_dict = dict()
        for file_block in self.file_block_list:
            file_block_dict[file_block.get_name()] = file_block
        for name in sorted(file_block_dict.keys()):
            file_block_store.append(None, [name, file_block_dict[name]])
        self.file_block_list_view.set_model(file_block_store)

    def get_selected_instru(self):
        model, tree_iter = self.instru_list_view.get_selection().get_selected()
        if tree_iter:
            return model.get_value(tree_iter, 1)
        return None

    def on_key_press(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=True)

    def on_key_release(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=False)

    def quit(self, wiget, event):
        AudioServer.close_all()
        Gtk.main_quit()

