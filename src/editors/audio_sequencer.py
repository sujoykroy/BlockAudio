from gi.repository import Gtk, Gdk
from ..audio_boxes import *
from ..audio_blocks import *
from .. import formulators
from ..commons import Point, Beat, KeyboardState, Rect
from ..commons import MusicNote, settings
from .. import gui_utils
from timed_group_page import TimedGroupPage
from file_instru_page import FileInstruPage
from formula_instru_page import FormulaInstruPage
from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import dump as XmlDump
from xml.etree.ElementTree import ElementTree as XmlTree
import os
import xml.etree.ElementTree as ET

from gi.repository import GObject
GObject.threads_init()

class AudioSequencer(Gtk.Window):
    def __init__(self, width=800, height=600,
                instru_list=None, timed_group_list=None, window_list=None):
        Gtk.Window.__init__(self, title="Sequencer", resizable=True)
        self.set_size_request(width, height)
        self.set_events(Gdk.EventMask.POINTER_MOTION_MASK)

        self.opened_audio_blocks = dict()
        self.opened_instrus = dict()
        self.beat = Beat(bpm=120/1,
                         sample_rate=AudioBlock.SampleRate,
                         pixel_per_sample=AudioBlockBox.PIXEL_PER_SAMPLE)
        self.tge_rect = Rect(0, 0, 1, 1)
        self.keyboard_state = KeyboardState()

        self.connect("delete-event", self.quit)
        self.connect("key-press-event", self.on_key_press)
        self.connect("key-release-event", self.on_key_release)

        if not instru_list:
            instru_list = []
        if not timed_group_list:
            timed_group = AudioTimedGroup()
            timed_group.set_name("Main")
            timed_group_list = []

        if window_list is None:
            window_list = []
        self.window_list = window_list

        self.instru_list = instru_list
        self.timed_group_list = timed_group_list
        self.filename = None

        self.instru_list_label = Gtk.Label("Instruments")
        self.instru_list_label.set_pattern("___________")
        self.instru_list_label.set_justify(Gtk.Justification.CENTER)

        #instru store
        self.instru_store = gui_utils.HarchTreeStore(str, object)
        instru_dict = dict()
        for instru in self.instru_list:
            instru_dict[instru.get_name()] = instru
        for name in sorted(instru_dict.keys()):
            self.instru_store.add(name, instru_dict[name])

        #intru list view
        self.instru_list_view = Gtk.TreeView()
        self.instru_list_view.set_model(self.instru_store)
        self.instru_list_view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0))
        self.instru_list_view.set_headers_visible(False)
        self.instru_list_view.connect(
            "row-activated", self.instru_list_view_row_activated)
        self.instru_list_view.set_model(self.instru_store)

        self.add_file_instru_button = Gtk.Button("Add File Instrument")
        self.add_file_instru_button.connect("clicked", self.add_file_instru_button_clicked)

        self.formula_list_label = Gtk.Label("Formulators")
        self.formula_list_label.set_pattern("___________")
        self.formula_combo_box = gui_utils.NameValueComboBox()
        self.formula_combo_box.set_value(None)
        self.add_formula_instru_button = Gtk.Button("Add Formula Instrument")
        self.add_formula_instru_button.connect("clicked", self.add_formula_instru_button_clicked)

        formulator_list = [formulators.TomTomFormulator]
        for i in xrange(len(formulator_list)):
            formulator = formulator_list[i]
            formulator_list[i] = [formulator.DISPLAY_NAME, formulator]
        formulator_list.append(["Customized", None])
        self.formula_combo_box.build_and_set_model(formulator_list)

        self.timed_group_list_label = Gtk.Label("Block Groups")
        self.timed_group_list_label.set_pattern("____________")
        self.timed_group_list_label.set_justify(Gtk.Justification.CENTER)

        #timed group store
        self.timed_group_store = gui_utils.HarchTreeStore(str, object)
        group_dict = dict()
        for group in self.timed_group_list:
            group_dict[group.get_name()] = group
        for name in sorted(group_dict.keys()):
            self.timed_group_store.add(name, group_dict[name])

        #timed group list view
        self.timed_group_list_view = Gtk.TreeView()
        self.timed_group_list_view.append_column(
            Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0))
        self.timed_group_list_view.set_headers_visible(False)
        self.timed_group_list_view.connect(
            "row-activated", self.timed_group_list_view_row_activated)
        self.timed_group_list_view.set_model(self.timed_group_store)

        self.add_block_group_button = Gtk.Button("Add Block Group")
        self.add_block_group_button.connect("clicked", self.add_block_group_button_clicked)


        #toolbox
        self.toolbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.open_file_button = Gtk.Button("Open")
        self.open_file_button.connect("clicked", self.open_file_button_clicked)

        self.save_file_button = Gtk.Button("Save")
        self.save_file_button.connect("clicked", self.save_file_button_clicked)

        self.save_as_file_button = Gtk.Button("Save As")
        self.save_as_file_button.connect("clicked", self.save_as_file_button_clicked)

        self.toolbox.pack_start(
                self.open_file_button, expand=False, fill=False, padding=2)
        self.toolbox.pack_start(
                self.save_file_button, expand=False, fill=False, padding=2)
        self.toolbox.pack_start(
                self.save_as_file_button, expand=False, fill=False, padding=2)

        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
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

        self.block_instru_notebook = Gtk.Notebook()
        self.block_instru_notebook.set_scrollable(True)

        self.root_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.root_paned.add1(self.blockinstru_box)
        self.root_paned.add2(self.block_instru_notebook)

        self.root_box.pack_start(self.toolbox, expand=False, fill=False, padding=5)
        self.root_box.pack_start(Gtk.Separator(), expand=False, fill=False, padding=5)
        self.root_box.pack_start(self.root_paned, expand=True, fill=True, padding=5)

        self.update_title()
        self.show_all()
        #self.load_block(self.timed_group_list[0])

    def rename_timed_group(self, timed_group, new_name):
        for tg in self.timed_group_list:
            if new_name == tg.get_name():
                return False
        timed_group.set_name(new_name)
        self.timed_group_store.rename_item(timed_group.get_name(), timed_group)
        return True

    def rename_instru(self, instru, new_name):
        for ins in self.instru_list:
            if new_name == ins.get_name():
                return False
        instru.set_name(new_name)
        self.instru_store.rename_item(instru.get_name(), instru)
        return True

    def add_page(self, page, name):
        if isinstance(page, TimedGroupPage):
            if page.audio_block.get_id() in self.opened_audio_blocks:
                return
            self.opened_audio_blocks[page.audio_block.get_id()] = page
        elif isinstance(page, FileInstruPage):
            if page.instru.get_id() in self.opened_instrus:
                return
            self.opened_instrus[page.instru.get_id()] = page

        page.init_show()
        widget = page.get_widget()

        close_button = gui_utils.CloseTabButton(self.notebook_tab_close_button_clicked, page)

        tab_label = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        tab_label.pack_start(page.get_tab_name_label(), expand=True, fill=True, padding=0)
        tab_label.pack_start(close_button, expand=False, fill=False, padding=5)
        tab_label.show_all()

        self.block_instru_notebook.append_page(widget, tab_label)
        self.block_instru_notebook.show()

    def update_title(self):
        filename = self.filename
        if not filename:
            filename = ""
        if len(filename)>100:
            filename = filename[:97] + "..."
        if filename:
            filename = ": " + filename
        self.set_title("BlockAudio " + filename)

    def save_file(self, filename):
        app = XmlElement("app")
        app.attrib["name"] = "{0}".format(settings.APP_NAME)
        app.attrib["version"] = "{0}".format(settings.APP_VERSION)

        root_elm = XmlElement("root")
        root_elm.append(app)

        active_instru_set = set()
        for block in self.timed_group_list:
            block_instru_set = block.get_instru_set()
            if not block_instru_set:
                continue
            active_instru_set = active_instru_set.union(block_instru_set)

        for instru in active_instru_set:
            root_elm.append(instru.get_xml_element())
        for block in self.timed_group_list:
            root_elm.append(block.get_xml_element())

        tree = XmlTree(root_elm)

        backup_file = None
        if os.path.isfile(filename):
            backup_file = filename + ".bk"
            os.rename(filename, backup_file)
        tree.write(filename)
        try:
            tree.write(filename)
            result = True
        except TypeError as e:
            if backup_file:
                os.rename(backup_file, filename)
                backup_file = None
        if backup_file:
            os.remove(backup_file)

    def load_file(self, filename):
        try:
            tree = ET.parse(filename)
        except IOError as e:
            return
        except ET.ParseError as e:
            return
        root_elm = tree.getroot()
        app = root_elm.find("app")
        if app is None or app.attrib.get("name", None) != settings.APP_NAME: return False

        loaded_instrus = dict()
        for instru_elm in root_elm.findall(AudioInstru.TAG_NAME):
            instru_type = instru_elm.get("type")
            if instru_type == AudioFileInstru.TYPE_NAME:
                instru = AudioFileInstru.create_from_xml(instru_elm)
            elif instru_type == AudioFormulaInstru.TYPE_NAME:
                instru = AudioFormulaInstru.create_from_xml(instru_elm)
            else:
                continue
            self.append_instru(instru)
            loaded_instrus[instru.get_name()] = instru

        loaded_blocks = dict()
        for block_elm in root_elm.findall(AudioBlock.TAG_NAME):
            block = self.load_block_from_xml(block_elm, root_elm, loaded_blocks, loaded_instrus)
            self.timed_group_list.append(block)
            self.timed_group_store.add(block.get_name(), block)

    def load_block_by_name(self, block_name, root_elm, loaded_blocks, loaded_instrus):
        if block_name in loaded_blocks:
            return loaded_blocks[block_name]
        for block_elm in root_elm.findall(AudioBlock.TAG_NAME):
            if block_name == block_elm.get("name"):
                return self.load_block_from_xml(
                    block_elm, root_elm, loaded_blocks, loaded_instrus)
        return None

    def load_block_from_xml(self, block_elm, root_elm, loaded_blocks, loaded_instrus):
        block_type = block_elm.get("type")
        block_name = block_elm.get("name")

        if block_name in loaded_blocks:
            return loaded_blocks[block_name]

        block = None
        if block_type == AudioTimedGroup.TYPE_NAME:
            linked_to = block_elm.get("linked_to")
            blocks = []
            if linked_to:
                linked_to = self.load_block_by_name(
                        linked_to, root_elm, loaded_blocks, loaded_instrus)
            else:
                for child_block_elm in block_elm.findall(AudioBlock.TAG_NAME):
                    child_block = self.load_block_from_xml(
                        child_block_elm, root_elm, loaded_blocks, loaded_instrus)
                    if not child_block:
                        continue
                    blocks.append(child_block)
            block = AudioTimedGroup.create_from_xml(block_elm, blocks, linked_to)
        elif block_type == AudioSamplesBlock.TYPE_NAME:
            instru_name = block_elm.get("instru")
            if not instru_name:
                return None
            instru = loaded_instrus.get(instru_name)
            if not instru:
                return None
            block = AudioSamplesBlock.create_from_xml(block_elm, instru)
        loaded_blocks[block.get_name()] = block
        return block

    def append_instru(self, instru):
        self.instru_list.append(instru)
        self.instru_store.add(instru.get_name(), instru)

    def notebook_tab_close_button_clicked(self, widget, page):
        page.cleanup()
        self.block_instru_notebook.remove(page.get_widget())

        if isinstance(page, TimedGroupPage):
            if page.audio_block.get_id() in self.opened_audio_blocks:
                del self.opened_audio_blocks[page.audio_block.get_id()]
        elif isinstance(page, FileInstruPage) or isinstance(page, FormulaInstruPage):
            if page.instru.get_id() in self.opened_instrus:
                del self.opened_instrus[page.instru.get_id()]

    def show_block(self, audio_block):
        self.add_page(
            TimedGroupPage(self, audio_block, self),
            audio_block.get_name()
        )

    def show_instru(self, instru):
        if not instru:
            return
        if isinstance(instru, AudioFileInstru):
            instru_page = FileInstruPage(self, instru)
        elif isinstance(instru, AudioFormulaInstru):
            instru_page = FormulaInstruPage(self, instru)
        self.add_page(instru_page, instru.get_name())

    def open_file_button_clicked(self, widget):
        filename = gui_utils.FileOp.choose_file(self, "open")
        if not filename:
            return
        if self.filename:
            win = AudioSequencer(window_list=self.window_list)
            win.start()
        else:
            win = self
        win.filename = filename
        win.load_file(filename)
        win.update_title()

    def save_file_button_clicked(self, widget):
        if not self.filename:
            filename = gui_utils.FileOp.choose_file(self, "save")
            if filename and not os.path.splitext(filename)[1]:
                filename = filename + settings.FILE_EXT
            self.filename = filename
        if not self.filename:
            return
        self.save_file(self.filename)
        self.update_title()

    def save_as_file_button_clicked(self, widget):
        filename = gui_utils.FileOp.choose_file(self, "save_as")
        if not filename:
            return
        if not os.path.splitext(self.filename)[1]:
            filename = filename + settings.FILE_EXT
        self.filename = filename
        self.save_file(self.filename)
        self.update_title()

    def add_file_instru_button_clicked(self, widget):
        filename = gui_utils.FileOp.choose_file(self, "open", "audio")
        if filename:
            instru = AudioFileInstru(filename=filename)
            self.append_instru(instru)


    def add_formula_instru_button_clicked(self, widget):
        formulator_class = self.formula_combo_box.get_value()
        instru = AudioFormulaInstru(formulator=formulator_class)
        self.instru_list.append(instru)
        self.instru_store.add(instru.get_name(), instru)

    def add_block_group_button_clicked(self, widget):
        timed_group = AudioTimedGroup()
        timed_group.set_duration_unit(AudioBlockTime.TIME_UNIT_BEAT, self.beat)
        timed_group.set_duration_value(1, self.beat)
        self.timed_group_list.append(timed_group)
        self.timed_group_store.add(timed_group.get_name(), timed_group)

    def instru_list_view_row_activated(self, tree_view, path, column):
        treeiter = tree_view.get_model().get_iter(path)
        if not treeiter:
            return
        instru = tree_view.get_model().get_value(treeiter, 1)
        self.show_instru(instru)

    def timed_group_list_view_row_activated(self, tree_view, path, column):
        treeiter = tree_view.get_model().get_iter(path)
        if not treeiter:
            return
        block = tree_view.get_model().get_value(treeiter, 1)
        self.show_block(block)

    def get_selected_instru(self):
        model, tree_iter = self.instru_list_view.get_selection().get_selected()
        if tree_iter:
            return model.get_value(tree_iter, 1)
        return None

    def get_selected_timed_group(self):
        model, tree_iter = self.timed_group_list_view.get_selection().get_selected()
        if tree_iter:
            return model.get_value(tree_iter, 1)
        return None

    def on_key_press(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=True)

    def on_key_release(self, widget, event):
        self.keyboard_state.set_keypress(event.keyval, pressed=False)

    def quit(self, wiget, event):
        self.window_list.remove(self)
        if not self.window_list:
            AudioServer.close_all()
            Gtk.main_quit()

    def start(self):
        self.window_list.append(self)
        if len(self.window_list) == 1:
            Gtk.main()

