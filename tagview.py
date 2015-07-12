from tkinter.ttk import Treeview, Frame
from tkinter import N, S, W, E
import os

import keybindings as kb
from tkgraphics import Gallery

class NameView(object):
    """Shows a treeview of unique names."""

    def __init__(self, master, names):
        self.widget = Treeview(master, columns=['name'])
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
        self._iids = dict()
        self._names = dict()
        for name in sorted(names):
            iid = self.widget.insert('', 'end', text=name)
            self._names[iid] = name
            self._iids[name] = iid

    def selection(self):
        return [self._names[iid] for iid in self.widget.selection()]

    def edit(self):
        self.widget.event_generate('<<NameViewEdit>>')

    def search(self):
        if len(self.widget.selection()) == 0:
            self.widget.selection_add(self.widget.focus())
        self.widget.event_generate('<<NameViewSearch>>')

    def append(self, names):
        for name in names:
            if name not in self._names.values():
                iid = self.widget.insert('', 'end', text=name)
                self._names[iid] = name
                self._iids[name] = iid

    def delete(self, name):
        self.widget.delete(self._iids[name])
        del self._names[self._iids[name]]
        del self._iids[name]

    def _focus(self, iid):
        self.widget.focus(iid)
        self.widget.see(iid)

    def focus_next(self):
        cur_iid = self.widget.focus()
        next_iid = self.widget.next(cur_iid)
        if next_iid == '':
            iids = self.widget.get_children()
            next_iid = iids[0]
        self._focus(next_iid)

    def focus_prev(self):
        cur_iid = self.widget.focus()
        prev_iid = self.widget.prev(cur_iid)
        if prev_iid == '':
            iids = self.widget.get_children()
            prev_iid = iids[-1]
        self._focus(prev_iid)

    def jump_to(self, name):
        try:
            iid = self._iids[name]
            self._focus(iid)
        except KeyError:
            pass

    def get_names(self):
        return tuple(self._names.values())

    def set(self, names):
        self.widget.delete(*self._iids.values())
        self._iids.clear()
        self._names.clear()
        for name in sorted(names):
            iid = self.widget.insert('', 'end', text=name)
            self._names[iid] = name
            self._iids[name] = iid

        

class TagView(NameView):

    def __init__(self, master, tags):
        super(TagView, self).__init__(master, tags)

    def append_tags(self, tags):
        tags = tuple(set(tags))
        super(TagView, self).append(tags)

    def get_tag_list(self):
        return super(TagView, self).get_names()

    def edit(self):
        self.widget.event_generate('<<TagViewEdit>>')

    def search(self):
        if len(self.widget.selection()) == 0:
            self.widget.selection_add(self.widget.focus())
        self.widget.event_generate('<<TagViewSearch>>')

