
import os
import subprocess
import mimetypes

from tkinter import Tk, Menu, N, S, W, E, HORIZONTAL, Toplevel, StringVar
from tkinter.ttk import PanedWindow, Entry, Label, Frame, Button

from db import FileDatabase
from tkgraphics import gallery_with_slideshow
from tagview import TagView
from gui2db import Gui2Db

import keybindings as kb

class Main(object):

    def __init__(self):
        root = Tk()
        self.paned_win = PanedWindow(root, orient=HORIZONTAL)
        self.root = self.paned_win
        root.title('GICM')
        root.focus_set()
        root.rowconfigure(0, weight=0)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        self.menubar = Frame(root)
        self.menubar.grid(row=0, column=0, sticky=(W, E))
        self.menubar['takefocus'] = False
        quit_button = Button(self.menubar, text='Quit', command=self.quit)
        quit_button.grid(row=0, column=0)
        self._menucolumn = 1
        self.views = list()
        self.cur_view = 0
        self.delete_current_view = lambda e: self.remove_view(self.views[self.cur_view]) 
        self.paned_win.grid(row=1, column=0, sticky=(N, S, W, E))
        self._root = root
        self._query = None
        self._accept_func = None

    def add_menubutton(self, label, action):
        button = Button(self.menubar, text=label, command=action)
        button.grid(row=0, column=self._menucolumn)
        self._menucolumn += 1

    def add_sidebar(self, view):
        self.sidebar = view
        self.paned_win.add(self.sidebar.widget, weight=1)
        self.sidebar.widget.focus_set()

    def new_view(self, view):
        self.views.append(view)
        if len(self.views) > 1:
            self.paned_win.forget(self.views[self.cur_view].widget)
        self.cur_view = len(self.views) - 1
        self.paned_win.add(view.widget, weight=5)

        view.widget.focus_set()

    def remove_view(self, view):
        self.views.remove(view)
        self.paned_win.forget(view.widget)
        if len(self.views) >= 1:
            self.views[-1].widget.focus_set()
            self.cur_view -= 1
            self.paned_win.add(self.views[self.cur_view].widget, weight=5)
        else:
            self.sidebar.widget.focus_set()

    def next_view(self):
        self.paned_win.forget(self.views[self.cur_view].widget)
        self.cur_view += 1
        if self.cur_view >= len(self.views):
            self.cur_view = 1
        new_view = self.views[self.cur_view]
        self.paned_win.add(new_view.widget, weight=5)
        new_view.widget.focus_set()

    def close_query(self):
        if self._query is not None:
            self._query.event_generate('<<MainQueryClose>>')
            self._query.destroy()
            self._query = None
            self._menucolumn -= 1

    def accept_query(self, event):
        if self._query is not None:
            if self._accept_func is not None:
                self._accept_func(event.widget.get(), event.widget.original_value)
                self.close_query()
            else:
                widget.event_generate('<<MainQueryAccept>>')

    def text_query(self, query_lable, original_text=None, accept_func=None):
        frame = Frame(self.menubar)
        label = Label(frame, text=query_lable)
        label.grid(column=0, row=0, sticky=(N, S))
        self._accept_func = accept_func

        entry = Entry(frame)
        if original_text is not None:
            entry.insert(0, original_text)
        entry.original_value = original_text
        entry.grid(column=1, row=0, sticky=(N,S,W,E))
        kb.make_bindings(kb.text_query, 
                {'accept': self.accept_query,
                 'cancel': lambda e: self.close_query()}, entry.bind)

        frame.grid(column=self._menucolumn, row=0)
        self._menucolumn += 1
        entry.focus_set()
        self._query = frame

    def display(self):
        self._root.mainloop()

    def quit(self):
        self._root.destroy()

if __name__ == "__main__":
    db = FileDatabase('winexperiment.sqlite')
    gui = Main()

    li = db.search_by_tags(['abstract'])[:100]

    glue = Gui2Db(db, gui)

    tags = db.list_tags()
    view = TagView(gui, tags)
    view.widget.bind('<<TagViewSearch>>', glue.search)
    view.widget.bind('<<TagViewEdit>>',
            lambda e: gui.text_query('Edit tag: ', e.widget.selection()[0]))

    paths = [os.path.join(d['path'], d['name']) for d in li]
    gal = gallery_with_slideshow(gui.root, paths, gui.new_view)
    gal.widget.bind('<Control-a>', lambda e: glue.add_tags_from_tagview(e, view))

    gui.root.bind_all('<Control-i>', lambda e: gui.text_query('Add tags: '))
    gui.root.bind_all('<<MainQueryAccept>>', glue.add_or_rename_tags)
    gui.root.bind_all('<Control-o>', glue.add_files)
    gui.root.bind_all('<Control-p>', glue.add_directory)
    gui.add_sidebar(view)
    gui.new_view(gal)
    gui.display()

