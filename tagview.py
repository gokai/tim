from tkinter.ttk import Treeview, Frame
from tkinter import N, S, W, E
import os

import keybindings as kb
from tkgraphics import Gallery

class TagView(object):

    def __init__(self, main, db, tags):
        self.main = main
        self.db = db
        self.view = Treeview(self.main.root, columns=['name'])
        self.view.column('name', width=50)
        self.view['show'] = 'tree'
        actions = {'edit': lambda e: self.edit(),
                'search': lambda e: self.search()
                }
        #TODO: keybindings
        #kb.make_bindings(kb.tagview, actions, self.view.bind)
        self.view.bind('e', self.edit)
        self.view.bind('<Double-1>', lambda e: self.search())
        for tag in sorted(tags):
            self.view.insert('', 'end', iid=tag, text=tag)

    def edit(self, s):
        self.view.event_generate('<<TagsChanged>>')

    def search(self):
        self.view.event_generate('<<TagViewSearch>>')


