from gi.repository import Gtk

class HarchTreeStore(Gtk.TreeStore):
    def __init__(self, *arg, **kwarg):
        super(HarchTreeStore, self).__init__(*arg, **kwarg)
        self.branches = dict()
        self.added_items = dict()

    def add(self, name, item):
        levels = name.split("/")
        name = levels[-1]
        levels = levels[:-1]
        parent = None
        for i in xrange(len(levels)):
            level_name = "/".join(levels[:i+1])
            if level_name not in self.branches:
                parent = self.append(parent, [levels[i] , None])
                self.branches[level_name] = parent
            else:
                parent = self.branches[level_name]
        new_iter = super(HarchTreeStore, self).append(parent, [name, item])
        self.added_items[item] = new_iter
        return new_iter

    def rename_item(self, new_name, item):
        self.remove(self.added_items[item])
        del self.added_items[item]
        self.add(new_name, item)

    def remove_item(self, item):
        print self.added_items.keys()
        self.remove(self.added_items[item])
        del self.added_items[item]
