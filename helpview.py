from tkinter.ttk import Treeview

import keybindings

class HelpView(object):

    def __init__(self, master):
        self.widget = Treeview(master, columns=['Key', 'Action'])
        self.widget['show'] = 'tree'
        self.add_group('Appwide', keybindings.appwide)
        self.add_group('Gallery', keybindings.gallery)
        self.add_group('Slideshow', keybindings.slideshow)
        self.add_group('Tagview', keybindings.tagview)
        self.add_group('Text query', keybindings.text_query)

    def add_group(self, name, keys):
        tid = self.widget.insert('', 'end', open=True, text = name)
        for key in keys:
            self.widget.insert(tid, 'end', values=[key, keys[key]])

