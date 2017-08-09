from gi.repository import Gtk

class NameValueComboBox(Gtk.ComboBox):
    def __init__(self):
        Gtk.ComboBox.__init__(self)
        renderer_text = Gtk.CellRendererText()
        self.pack_start(renderer_text, True)
        self.add_attribute(renderer_text, "text", 0)
        self.name_index = 0
        self.value_index = 0
        self.values_dict = dict()

    def build_and_set_model(self, values):
        self.values_dict.clear()
        if values:
            if type(values[0]) is not list:
                fields = [str]
                store = Gtk.ListStore(str)
                for value in values:
                    store.append([value])
                    self.values_dict[value] = value
                self.value_index = self.name_index = 0
            else:
                store = Gtk.ListStore(str, object)
                for value in values:
                    store.append(value)
                    self.values_dict[value[-1]] = value[0]
                self.name_index = 0
                self.value_index = 1
        else:
            store = Gtk.ListStore(str)
        self.set_model(store)
        self.set_id_column(self.name_index)

    def set_value(self, value):
        if value in self.values_dict:
            self.set_active_id(self.values_dict[value])

    def get_value(self, default=None):
        tree_iter = self.get_active_iter()
        if not tree_iter: return default
        model = self.get_model()
        return model[tree_iter][self.value_index]

