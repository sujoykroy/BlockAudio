from gi.repository import Gtk

class TextInputDialog(Gtk.Dialog):
    def __init__(self, parent, title, text, input_text="", width=400, height = 200):
        Gtk.Dialog.__init__(self, title, parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(width, height)

        box = self.get_content_area()

        label = Gtk.Label()
        label.set_markup(text)
        box.pack_start(label, expand=False, fill=False, padding= 40)

        self.entry = Gtk.Entry()
        self.entry.set_text(input_text)
        self.entry.set_alignment(.5)
        box.pack_start(self.entry, expand=False, fill=False, padding= 0)
        self.show_all()

    def get_input_text(self):
        return self.entry.get_text()

class YesNoDialog(Gtk.Dialog):
    def __init__(self, parent, title, text, width=400, height = 100):
        Gtk.Dialog.__init__(self, title, parent, 0,
            (Gtk.STOCK_YES, Gtk.ResponseType.YES,
                 Gtk.STOCK_NO, Gtk.ResponseType.NO))
        self.set_default_size(width, height)

        box = self.get_content_area()

        label = Gtk.Label()
        label.set_markup(text)
        box.pack_start(label, expand=False, fill=False, padding= 40)

        self.show_all()

class NoticeDialog(Gtk.Dialog):
    def __init__(self, parent, text, title=None, width=400, height = 100):
        Gtk.Dialog.__init__(self, title, parent, 0, (Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(width, height)

        box = self.get_content_area()

        label = Gtk.Label()
        label.set_markup(text)
        box.pack_start(label, expand=False, fill=False, padding= 40)

        self.show_all()
        self.run()
        self.destroy()

