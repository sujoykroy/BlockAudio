from gi.repository import Gtk, GObject
import Queue
from ..audio_blocks import AudioServer, AudioFileBlock

class FileOp(object):
    @staticmethod
    def choose_file(parent, purpose, file_types=[["Block Audio", "*.blau.xml"]], filename=None):
        if purpose == "save":
            title = "Save"
            action = Gtk.FileChooserAction.SAVE
            ok_key = Gtk.STOCK_SAVE
        elif purpose == "save_as":
            title = "Save As"
            action = Gtk.FileChooserAction.SAVE
            ok_key = Gtk.STOCK_SAVE_AS
        elif purpose == "open":
            title = "Open file"
            action = Gtk.FileChooserAction.OPEN
            ok_key = Gtk.STOCK_OPEN

        dialog = FileChooserDialog(title, parent, action,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, ok_key, Gtk.ResponseType.OK))
        if filename:
            dialog.set_filename(filename)
        if purpose in ("save", "save_as"):
            dialog.props.do_overwrite_confirmation = True
        if file_types == "audio":
            file_types = [["Audio", "audio/*"]]
            #dialog.set_preview_audio(True)

        for file_name, mime_type in file_types:
            if file_name == "Audio":
                dialog.set_preview_audio(not True)
            filter_text = Gtk.FileFilter()
            filter_text.set_name("{0} files".format(file_name))
            if mime_type.find("/")>0:
                filter_text.add_mime_type(mime_type)
            else:
                filter_text.add_pattern(mime_type)
            dialog.add_filter(filter_text)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        else:
            filename = None
        dialog.destroy()
        return filename


class FileSelect(Gtk.HBox):
    __gsignals__ = {
        'file-selected': (GObject.SIGNAL_RUN_FIRST, None,
                      tuple())
    }

    def __init__(self, file_types=[]):
        Gtk.HBox.__init__(self)
        self.selection_entry = Gtk.Entry()
        self.selection_entry.connect("activate", self.selection_entry_activated)
        #self.selection_entry.set_editable(False)

        self.select_button = Gtk.Button("Open")
        self.select_button.connect("clicked", self.select_button_clicked)

        self.refresh_button = Gtk.Button("Reload")
        self.refresh_button.connect("clicked", self.refresh_button_clicked)

        self.file_types = file_types
        self.set_filename(None)

        self.pack_start(self.selection_entry, expand=True, fill=True, padding=0)
        self.pack_end(self.refresh_button, expand=False, fill=True, padding=0)
        self.pack_end(self.select_button, expand=False, fill=True, padding=0)

    def set_filename(self, filename):
        if filename is None:
            filename = ""
        self.filename = filename
        self.selection_entry.set_text(filename)
        self.selection_entry.set_position(-1)

    def get_filename(self):
        return self.filename

    def selection_entry_activated(self, widget):
        self.set_filename(self.selection_entry.get_text())
        self.emit("file-selected")

    def select_button_clicked(self, widget):
        filename = FileOp.choose_file(
                widget.get_toplevel(), "open", self.file_types, filename=self.filename)
        if filename:
            self.set_filename(filename)
            self.emit("file-selected")

    def refresh_button_clicked(self, widget):
        self.set_filename(self.filename)
        self.emit("file-selected")

    def show(self):
        super(FileSelect, self).show()
        self.show_all()

    def hide(self):
        super(FileSelect, self).hide()
        self.select_button.hide()
        self.refresh_button.hide()
        self.selection_entry.hide()

class FileChooserDialog(Gtk.FileChooserDialog):
    def __init__(self, *args, **kwargs):
        Gtk.FileChooserDialog.__init__(self, *args, **kwargs)
        self.connect("update-preview", self.file_selection_changed)
        self.file_type = None
        self.audio_file_block = None
        self.preview_audio = False

    def set_preview_audio(self, value):
        self.preview_audio = value
        if self.preview_audio:
            self.audio_server = AudioServer.get_default()

    def file_selection_changed(self, widget):
        if self.preview_audio:
            if self.audio_file_block:
                self.audio_server.remove_block(self.audio_file_block)
            self.audio_file_block = None

            filename = self.get_filename()
            if filename:
                self.audio_file_block = AudioFileBlock(filename, preload=False)
                self.audio_file_block.set_no_loop()
                self.audio_file_block.play()
                self.audio_server.play()
                self.audio_server.add_block(self.audio_file_block)

    def destroy(self):
        if self.audio_file_block:
            self.audio_server.remove_block(self.audio_file_block)
        super(FileChooserDialog, self).destroy()
