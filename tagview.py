from tkinter.ttk import Treeview
import os

import keybindings as kb
from tkgraphics import Gallery

class TagView(object):

    def __init__(self, main, db, tags):
        self.main = main
        self.db = db
        self.view = Treeview(main.root, columns=['name'])
        self.view.column('name', width=50)
        self.view['show'] = 'tree'
        actions = {'edit': lambda e: self.edit()}
        #TODO: keybindings
        #kb.make_bindings(kb.tagview, actions, self.view.bind)
        self.view.bind('e', self.edit)
        for tag in sorted(tags):
            self.view.insert('', 'end', iid=tag, text=tag)

    def edit(self, s):
        self.view.event_generate('<<TagsChanged>>')

