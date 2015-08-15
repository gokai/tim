
import os
import subprocess
import mimetypes
import logging
logger = logging.getLogger(__name__)

from tkinter import Tk, Menu, N, S, W, E, HORIZONTAL, Toplevel, StringVar
from tkinter.ttk import PanedWindow, Entry, Label, Frame, Button, Notebook

from tkgraphics import gallery_with_slideshow
from tagview import TagView
from gui2db import Gui2Db

import keybindings as kb

class Main(object):

    def __init__(self):
        root = Tk()
        root.title('GICM')
        root.focus_set()
        root.rowconfigure(0, weight=0)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        self._root = root

        self.menubar = Frame(root)
        self.menubar.grid(row=0, column=0, sticky=(W, E))
        self.menubar['takefocus'] = False

        quit_button = Button(self.menubar, text='Quit', command=self.quit)
        quit_button.grid(row=0, column=0)

        self._menucolumn = 1
        self.views = list()

        self.paned_win = PanedWindow(root, orient=HORIZONTAL)
        self.paned_win.grid(row=1, column=0, sticky=(N, S, W, E))

        self._query = None
        self._accept_func = None

        self.sidebar_views = dict()
        self.sidebar_count = 0
        self.sidebar = PanedWindow(self.paned_win)
        self.paned_win.add(self.sidebar, weight=1)
        
        self.tabs = Notebook(self.paned_win)
        self.tabs.enable_traversal()
        self.paned_win.add(self.tabs, weight=5)
        self.root = self.tabs

    def add_menubutton(self, label, action):
        button = Button(self.menubar, text=label, command=action)
        button.grid(row=0, column=self._menucolumn)
        self._menucolumn += 1

    def add_sidebar(self, view, name):
        self.sidebar_views[name] = view
        self.sidebar.add(view.widget, weight=1)
        view.widget.focus_set()
        self.sidebar_count += 1
        if self.sidebar_count == 1:
            self.sidebar_views['main'] = view

    def remove_sidebar_view(self, name):
        self.sidebar.forget(self.sidebar_views[name].widget)
        self.sidebar_count -= 1
        del self.sidebar_views[name]
        if self.sidebar_count == 0:
            del self.sidebar_views['main']

    def get_sidebar_view(self, name):
        return self.sidebar_views.get(name)

    def focus_sidebar(self):
        if 'main' in self.sidebar_views.keys():
            self.sidebar_views['main'].widget.focus_set()

    def focus_main_view(self):
        self.get_current_view().widget.focus_set()

    def new_view(self, view):
        self.views.append(view)
        self.tabs.add(view.widget, text=" {}.".format(self.tabs.index('end')))
        self.tabs.select(view.widget)

        view.widget.focus_set()
        self.view_changed()

    def remove_view(self, view):
        self.views.remove(view)
        self.tabs.forget(view.widget)
        if len(self.views) >= 1:
            widget = self.views[-1].widget
            self.tabs.select(widget)
            widget.focus_set()
        else:
            self.sidebar_views['main'].widget.focus_set()
        self.view_changed()

    def delete_current_view(self, event):
        if self.tabs.index('end') > 0:
            self.remove_view(self.get_current_view())

    def close_query(self):
        if self._query is not None:
            self._query.event_generate('<<MainQueryClose>>')
            self._query.destroy()
            self._query = None
            self._accept_func = None
            self._menucolumn -= 1

    def accept_query(self, event):
        if self._query is not None:
            if self._accept_func is not None:
                self._accept_func(event.widget.get(), event.widget.original_value)
                self.close_query()
            else:
                event.widget.event_generate('<<MainQueryAccept>>')

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

    def get_current_view(self):
        if self.tabs.index('end') > 0:
            return self.views[self.tabs.index('current')]
        else:
            return self.sidebar_views['main']

    def view_changed(self):
        self._root.event_generate('<<MainViewChanged>>')

    def display(self):
        self._root.mainloop()

    def quit(self):
        self._root.destroy()

