from tkinter.ttk import Treeview, Frame
from tkinter import N, S, W, E
import os

import keybindings as kb
from tkgraphics import Gallery

class TagView(object):

    def __init__(self, main, db, tags):
        self.main = main
        self.db = db
        self.widget = Treeview(self.main.root, columns=['name'])
        self.widget.column('name', width=50)
        self.widget['show'] = 'tree'
        actions = {'edit': lambda e: self.edit(),
                'search': lambda e: self.search()
                }
        #TODO: keybindings
        #kb.make_bindings(kb.tagview, actions, self.view.bind)
        self.widget.bind('e', self.edit)
        self.widget.bind('<Double-1>', lambda e: self.search())
        for tag in sorted(tags):
            self.widget.insert('', 'end', iid=tag, text=tag)

    def edit(self, s):
        self.widget.event_generate('<<TagsChanged>>')

    def search(self):
        self.widget.event_generate('<<TagViewSearch>>')

    def append_tags(self, tags):
        for tag in tags:
            # no reason to show same tag twice
            if not self.widget.exists(tag):
                self.widget.insert('', 'end', iid=tag, text=tag)


