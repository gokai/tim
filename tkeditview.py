
import os
from math import floor

from tkinter import *
from tkinter.ttk import *

import keybindings as kb
from tkgraphics import Gallery

class EditView(PanedWindow):

    def __init__(self, root, items, update, image_view, full_view):
        self.items = items
        self.update = update
        self.full_view = full_view
        super(EditView, self).__init__(root)
        self.load_pos = 0
        self.focused = 0
        self.frames = []
        self.IV = image_view
        self.common_tags = set()
        self.style = Style()
        self.style.configure('Focus.TLabelframe', relief='ridge')
        actions = {'focus_gallery':lambda e: self.gal.focus_set(),
                'focus_tags':lambda e: self.tags.focus_set()
                }
        kb.make_bindings(kb.editview, actions, self.bind)
        self.show_common_tags()
        self.winfo_height = lambda: self.winfo_height() - 250
        gal_frame = Frame(self)
        self.gal = Gallery(gal_frame,
                [os.path.join(item['path'], item['name']) for item in self.items],
                (250, 250), full_view)
        self.gal.grid(column=0, row=0, sticky=(N,S,W,E))
        gal_frame.columnconfigure(0, weight=1)
        gal_frame.rowconfigure(0, weight=1)
        self.add(gal_frame)

    def show_common_tags(self):
        for tags in (item['tags'] for item in self.items):
            self.common_tags.update(tags)

        for item in self.items:
            self.common_tags.intersection_update(item['tags'])
        frame = LabelFrame(self, text='Common tags')
        #frame.grid(row=0, column=0,sticky=(N, S, W, E))
        self.add(frame)
        frame['style'] = 'Focus.TLabelframe'
        self.frames.append(frame)
        for num,tag in enumerate(self.common_tags):
            label = Label(frame, text=tag)
            label.grid(row=0, column=num)

