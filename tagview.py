from tkinter.ttk import Treeview, Frame
from tkinter import N, S, W, E
import os

import keybindings as kb
from tkgraphics import Gallery

class TagView(object):

    def __init__(self, main, tags):
        self.main = main
        self.widget = Treeview(self.main.root, columns=['name'])
        self.widget.column('name', width=50)
        self.widget['show'] = 'tree'
        actions = {'edit': lambda e: self.edit(),
                'search': lambda e: self.search(),
                'focus_next': lambda e: self.focus_next(),
                'focus_prev': lambda e: self.focus_prev(),
                'select': lambda e: self.widget.selection_toggle(self.widget.focus()),
                'clear_selection': lambda e: self.widget.selection_set([])
                }
        kb.make_bindings(kb.tagview, actions, self.widget.bind)
        for tag in sorted(tags):
            self.widget.insert('', 'end', iid=tag, text=tag)

    def edit(self):
        self.widget.event_generate('<<TagViewEdit>>')

    def search(self):
        if len(self.widget.selection()) == 0:
            self.widget.selection_add(self.widget.focus())
        self.widget.event_generate('<<TagViewSearch>>')

    def append_tags(self, tags):
        for tag in tags:
            # no reason to show same tag twice
            if not self.widget.exists(tag):
                self.widget.insert('', 'end', iid=tag, text=tag)


    def focus_next(self):
        cur_iid = self.widget.focus()
        next_iid = self.widget.next(cur_iid)
        if next_iid == '':
            iids = self.widget.get_children()
            next_iid = iids[0]
        self.widget.focus(next_iid)
        self.widget.see(next_iid)

    def focus_prev(self):
        cur_iid = self.widget.focus()
        prev_iid = self.widget.prev(cur_iid)
        if prev_iid == '':
            iids = self.widget.get_children()
            prev_iid = iids[-1]
        self.widget.focus(prev_iid)
        self.widget.see(prev_iid)
        
