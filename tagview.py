from tkinter.ttk import Treeview

import keybindings as kb

class TagView(object):

    def __init__(self, main, tags):
        self.tags = sorted(tags)
        self.main = main
        self.view = Treeview(main.root, columns=["name"])
        actions = {'search': lambda e: self.search(),
                   'edit': lambda e: self.edit()}
        #TODO: keybindings
        #kb.make_bindings(kb.tagview, actions, self.view.bind)
        self.view['show'] = 'tree'
        for tag in self.tags:
            self.view.insert('', 'end', iid=tag, text=tag)

    def search(self):
        pass

    def edit(self):
        pass

