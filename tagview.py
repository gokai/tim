from tkinter.ttk import Treeview, Frame, Scrollbar, Label
from tkinter import N, S, W, E
import os
import logging
logger = logging.getLogger(__name__)

import keybindings as kb
class NameView(object):
    """Shows a treeview of unique names."""

    def __init__(self, master, names, title="", counts=None):
        self.widget = Frame(master)
        if title != "":
            self.title = Label(self.widget, text=title) 
            self.title.grid(row=0, column=0)
        self._tree = Treeview(self.widget, columns='count')
        self._tree.grid(row=1, column=0, sticky=(N,S,W,E))
        self._tree.view = self
        self.widget.columnconfigure(0, weight=1)
        self.widget.rowconfigure(0,weight=0)
        self.widget.rowconfigure(1,weight=1)
        self._tree.column('count', width=5)
        self._tree['show'] = 'tree'
        self.widget.bind = self._tree.bind
        self._iids = dict()
        self._names = dict()
        self._filtered = list()
        self.widget.focus_set = self._tree.focus_set
        for i, name in enumerate(names):
            c = 0
            if counts is not None:
                c = counts[i]
            iid = self._tree.insert('', 'end', text=name, values=(c,))
            self._names[iid] = name
            self._iids[name] = iid
        self._scroll = Scrollbar(self.widget, command=self._tree.yview)
        self._tree['yscrollcommand'] = self._scroll.set
        self._scroll.grid(row=1, column=1, sticky=(N, S))
        self.widget.columnconfigure(1, weight=0)
        kb.bind('nameview', (self, ), self._tree.bind)

    def filter(self, prefix):
        """Only show names starting with prefix."""
        self.clear_filter()
        if prefix == '':
            return
        for name in self._iids:
            if not name.startswith(prefix):
                iid = self._iids[name]
                index = self._tree.index(iid)
                self._tree.detach(iid)
                self._filtered.append((iid, index))

    def clear_filter(self):
        self.set(sorted(self._iids))
        self._filtered = list()

    def selection(self):
        logger.debug('Selection: %s', self._tree.selection())
        return [self._names[iid] for iid in self._tree.selection()]

    def select(self):
        self._tree.selection_toggle(self._tree.focus())

    def clear_selection(self):
        self._tree.selection_set('')

    def edit(self):
        self._tree.event_generate('<<NameViewEdit>>')

    def search(self):
        if len(self._tree.selection()) == 0:
            self._tree.selection_add(self._tree.focus())
        self._tree.event_generate('<<NameViewSearch>>')

    def append(self, names):
        logger.debug('Append names: %s', names)
        for name in names:
            if name not in self._names.values():
                iid = self._tree.insert('', 'end', text=name)
                self._names[iid] = name
                self._iids[name] = iid

    def delete(self, name):
        self._tree.delete(self._iids[name])
        del self._names[self._iids[name]]
        del self._iids[name]

    def _focus(self, iid):
        self._tree.focus(iid)
        self._tree.see(iid)

    def focus_next(self):
        cur_iid = self._tree.focus()
        next_iid = self._tree.next(cur_iid)
        if next_iid == '':
            iids = self._tree.get_children()
            if len(iids) > 0:
                next_iid = iids[0]
        self._focus(next_iid)

    def focus_prev(self):
        cur_iid = self._tree.focus()
        prev_iid = self._tree.prev(cur_iid)
        if prev_iid == '':
            iids = self._tree.get_children()
            if len(iids) > 0:
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
        self._tree.delete(*self._iids.values())
        self._iids.clear()
        self._names.clear()
        for name in sorted(names):
            iid = self._tree.insert('', 'end', text=name)
            self._names[iid] = name
            self._iids[name] = iid

        

class TagView(NameView):

    def __init__(self, master, tags, title=""):
        names, counts = list(), list()
        for t in sorted(tags, key=lambda s: s['name']):
            names.append(t['name'])
            counts.append(t['file_count'])
        super(TagView, self).__init__(master, names, title, counts)

    def append_tags(self, tags):
        tags = tuple(set(tags))
        super(TagView, self).append(tags)

    def get_tag_list(self):
        return super(TagView, self).get_names()

    def edit(self):
        self._tree.event_generate('<<TagViewEdit>>')

    def search(self):
        if len(self._tree.selection()) == 0:
            self._tree.selection_add(self._tree.focus())
        self._tree.event_generate('<<TagViewSearch>>')

