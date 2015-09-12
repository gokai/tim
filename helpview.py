from tkinter.ttk import Treeview

import keybindings

class HelpView(object):

    def __init__(self, master):
        self.widget = Treeview(master, columns=['Key', 'Action'])
        self.widget['show'] = 'tree'
        self.add_group('Appwide', keybindings.config['mainview'])
        self.add_group('Gallery', keybindings.config['gallery'])
        self.add_group('Slideshow', keybindings.config['slideshow'])
        self.add_group('Tagview', keybindings.config['nameview'])
        self.add_group('Text query', keybindings.config['text_query'])

    def add_group(self, name, keys):
        tid = self.widget.insert('', 'end', open=True, text = name)
        for key in keys:
            self.widget.insert(tid, 'end', values=[key, keys[key]])

    def close(self):
        pass

