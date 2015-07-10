
__author__  = "tachara (tortured.flame@gmail.com)"

import os
import sys
import warnings
from math import floor
from collections import namedtuple

try:
    from Tkinter import *
    from ttk import *
except ImportError:
    from tkinter import *
    from tkinter.ttk import *

from PIL import Image
from PIL.ImageTk import PhotoImage

import keybindings as kb

Cursor = namedtuple('Cursor', ['column', 'row', 'prev_item'])
def resize(image, target_height, target_width):
    image.thumbnail((target_width, target_height), Image.BILINEAR)

def gallery_with_slideshow(root, paths, new_view):
    gal = Gallery(root, paths, (250,250), 
        lambda s: new_view(SlideShow(root, s)))
    return gal

# Change DecompressionBombWarning in to an error
# allows better handling.
warnings.simplefilter('error', Image.DecompressionBombWarning)

class SlideShow(object):

    def __init__(self, root, paths, pos=0):
        self.paths = paths
        self.img = paths[pos]
        self.pos = pos
        self.widget = Label(root, takefocus=True)
        self.root = root
        self.make_view()
        self.widget.bind('<Expose>', lambda e: self.reload())
        actions = {'next':lambda e: self.next(), 'prev':lambda e: self.prev(),
                'reload':lambda e: self.reload()}
        kb.make_bindings(kb.slideshow, actions, self.widget.bind)

    def reload(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if self._pil_image is None or h != self.prev_h or w != self.prev_w:
            self.prev_h = h
            self.prev_w = w
            if self._pil_image == None:
                self._pil_image = Image.open(self.img)
            img = self._pil_image.copy()
            resize(img, h, w)
            self.photo = PhotoImage(img)
            self.widget['image'] = self.photo

    def make_view(self):
        self._tid = None
        self._pil_image = None
        self.prev_w = 0
        self.prev_h = 0
        self.widget['anchor'] = CENTER
        self.reload()

    def next(self):
        self.pos += 1
        if self.pos >= len(self.paths):
            self.pos = 0
        self.img = self.paths[self.pos]
        self._pil_image = None
        self.reload()
        self.widget.event_generate('<<SlideShowNext>>')
        if self._tid is not None:
            self.widget.after_cancel(self._tid)
            self._tid = self.widget.after(self.delay, self.next)

    def prev(self):
        self.pos -= 1
        if self.pos < 0:
            self.pos = len(self.paths) - 1
        self.img = self.paths[self.pos]
        self._pil_image = None
        self.reload()
        self.widget.event_generate('<<SlideShowPrev>>')
        if self._tid is not None:
            self.widget.after_cancel(self._tid)
            self._tid = self.widget.after(self.delay, self.next)

    def start(self, delay):
        self.delay = delay*1000
        self._tid = self.widget.after(self.delay, self.next)

    def stop(self):
        self.widget.after_cancel(self._tid)
        self._tid = None

    def selection(self):
        return [self.paths[self.pos],]


    
class Gallery(object):
    LIMIT = 1000

    def __init__(self, root, paths, thumb_size, activate_func):
        """thumb_size = (w, h)"""
        self.paths = paths
        self.thumb_w = thumb_size[0]
        self.thumb_h = thumb_size[1]
        self.photos = list()
        self._selection = set()
        self.widget = Canvas(root)
        self.make_view()
        self.make_bindings()
        self.activate_func = activate_func
        self.widget.configure(takefocus=1)
        self.loaded = 0

    def make_bindings(self):
        self.widget.bind('<Expose>', lambda e: self.reload())
        actions = {'slide': self.activate,
                'clear_selection': lambda e: self.clear_selection(),
                'cursor_up':self.cursor_up,
                'cursor_right':self.cursor_right,
                'cursor_left':self.cursor_left,
                'cursor_down':self.cursor_down,
                'load_more':lambda e: self.continue_loading()}
        self.widget.bind('<Button-4>', self.scroll)
        self.widget.bind('<Button-5>', self.scroll)
        self.widget.bind('<MouseWheel>', self.scroll)
        kb.make_bindings(kb.gallery, actions, self.widget.bind)

    def make_view(self):
        self.style = Style()
        self.style.configure('Gallery.TLabel', padding=3)
        self.style.configure('Cursor.Gallery.TLabel', background='red')
        self.style.configure('Selected.Gallery.TLabel', background='blue')
        self.widget['confine'] = True
        self.prev_w = self.widget.winfo_width()
        self.load_pos = 0
        self.row = 0
        self.column = 0
        self.cursor = Cursor(-1,-1,-1)
        self.max_columns = self.calculate_max_columns()
        self.widget.after(100, self.load_next)

    def activate(self, e):
        self.activate_func(self.selection())
        self.widget.focus_set()

    def get_path(self, item_id):
        return self.paths[item_id]

    def selection(self):
        paths = [self.paths[i] for i in self._selection]
        return paths

    def clear_selection(self):
        self.widget.dtag('selected', 'selected')
        for index in self._selection:
            self.set_state(self.photos[index], 'normal')
        self._selection.clear()

    def button_callback(self, event, item, column, row):
        prev_item = self.photos[self.cursor.prev_item]
        self.remove_cursor(prev_item, event.state)
        self.set_cursor(item, column, row)

    def scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self.widget.yview(SCROLL, -1, UNITS)
        elif event.num == 5 or event.delta < 0:
            self.widget.yview(SCROLL, 1, UNITS)

    def reload(self):
        w = self.widget.winfo_width()
        if w != self.prev_w:
            self.prev_w = w
            self.max_columns = self.calculate_max_columns()
            self.repos = 0
            self.repos_col = 0
            self.repos_row = 0
            self.widget.after_idle(self.reposition_next)

    def reposition_next(self):
        if len(self.photos) > 0:
            photo = self.photos[self.repos]
            new_x, new_y = self.calculate_pos(self.repos_col, self.repos_row)
            self.widget.coords(photo.cid, new_x, new_y)
            if self.repos == self.cursor.prev_item:
                self.cursor = Cursor(self.repos_col, self.repos_row, self.repos)
            col, row = self.repos_col, self.repos_row
            self.widget.tag_bind(photo.cid, '<Button-1>',
                    lambda e: self.button_callback(e, photo, col, row))
            self.repos_col += 1

        if self.repos_col >= self.max_columns:
            self.repos_row += 1
            self.repos_col = 0
        if self.repos < len(self.photos) - 1:
            self.repos += 1
            self.widget.after_idle(self.reposition_next)

    def calculate_max_columns(self):
        w = self.widget.winfo_width()
        return floor(w/(self.thumb_w + 8))

    def calculate_pos(self, column, row):
        x = column * self.thumb_w + self.thumb_w/2 + 8*column + 5
        y = row * self.thumb_h + self.thumb_h/2 + 8*row + 5
        return x,y

    def load_next(self):
        try:
            img = Image.open(self.paths[self.load_pos])
            resize(img, self.thumb_h, self.thumb_w)
            photo = PhotoImage(img)
            col, row = self.column, self.row
            self.photos.append(photo)
            x, y = self.calculate_pos(self.column, self.row)
            photo.cid = self.widget.create_image(x, y, image=photo)
            photo.index = self.load_pos
            self.widget.tag_bind(photo.cid, '<Button-1>', lambda e: self.button_callback(e, photo, col, row))
            self.widget.tag_bind(photo.cid, '<Double-Button-1>', self.activate)
            self.widget.addtag_withtag('photo', photo.cid)
            self.column += 1
            self.loaded += 1
        except OSError:
            self.load_pos += 1
        except Image.DecompressionBombWarning:
            self.lead_pos += 1

        if self.column >= self.max_columns:
            self.row += 1
            self.column = 0
        if self.load_pos < len(self.paths) - 1 and self.loaded < self.LIMIT:
            self.load_pos += 1
            self.widget.after_idle(self.load_next)
        elif self.loaded >= self.LIMIT:
            self.loaded = 0
            x, y = self.calculate_pos(self.column, self.row)
            button = Button(self.widget, text='Load More', command=self.continue_loading)
            cid = self.widget.create_window(x, y, window=button)
            self.widget.addtag_withtag('loadbutton', cid)
        self.widget['scrollregion'] = self.widget.bbox('all')

    def continue_loading(self):
        if self.load_pos < len(self.paths) - 1:
            self.load_pos += 1
            self.widget.delete('loadbutton')
            self.widget.after_idle(self.load_next)

    def cursor_to_index(self, row, column):
        return row * self.max_columns + column 

    def max_cursor_position(self):
        row = floor((len(self.photos) - 1)/self.max_columns)
        column = (len(self.photos) - 1 - row * self.max_columns)
        return (row, column)

    def cursor_up(self, e):
        row = self.cursor.row - 1
        column = self.cursor.column
        if row < 0:
            row = 0
        self.move_cursor(column, row, e.state)

    def cursor_down(self, e):
        row = self.cursor.row + 1
        column = self.cursor.column
        self.move_cursor(column, row, e.state)

    def cursor_right(self, e):
        row = self.cursor.row
        column = self.cursor.column + 1
        if column >= self.max_columns:
            column = 0
            row += 1
        self.move_cursor(column, row, e.state)

    def cursor_left(self, e):
        row = self.cursor.row
        column = self.cursor.column - 1
        if column < 0:
            column = self.max_columns - 1
            row -= 1
        self.move_cursor(column, row, e.state)

    def move_cursor(self, column, row, state = 0x0):
        prev_item = self.photos[self.cursor.prev_item]
        if self.cursor.prev_item != -1:
            self.remove_cursor(prev_item, state)
        new_index = self.cursor_to_index(row, column)
        if new_index >= len(self.photos):
            row, column = self.max_cursor_position()
            new_index = len(self.photos) - 1
        elif new_index < 0:
            row, column = 0, 0
            new_index = 0
        item = self.photos[new_index]
        self.set_cursor(item, column, row)

    def set_cursor(self, item, column, row, index=None):
        self.set_state(item, 'active')
        self.cursor = Cursor(column, row, index or row*self.max_columns + column)
        self.widget.addtag_withtag('selected', item.cid)
        self.view_item(item)
        self._selection_add(item)

    def remove_cursor(self, item, state):
        # control key was down -> selection
        if state & 0x0004:
            self.set_state(item, 'selected')
        else:
            if 'selected' in self.widget.gettags(item.cid) and item.index in self._selection:
                self._selection_remove(item)
            self.set_state(item, 'normal')
            self.widget.dtag(item.cid, 'selected')

    def _selection_add(self, item):
        self._selection.add(item.index)
        self.widget.event_generate('<<GallerySelectionChanged>>')

    def _selection_remove(self, item):
        self._selection.remove(item.index)

    def set_state(self, item, state):
        color = ''
        if state == 'selected':
            color = 'blue'
        elif state == 'active':
            color = 'red'

        old_rect = getattr(item, 'rectangle_id', '')
        if old_rect != '':
            self.widget.delete(old_rect)
        bbox = self.widget.bbox(item.cid)
        item.rectangle_id = self.widget.create_rectangle(bbox[0], bbox[1], bbox[2], bbox[3], outline=color, width=8)
        self.widget.tag_lower(item.rectangle_id, item.cid)

    def view_item(self, item):
        self.widget['scrollregion'] = self.widget.bbox('all')
        bbox = self.widget.bbox(item.cid)
        max_y = self.widget.bbox('all')[3]
        max_visible_y = self.widget.canvasy(self.widget.winfo_height())
        min_visible_y = self.widget.canvasy(0)
        top = bbox[1]
        bottom = bbox[3]
        if bottom > max_visible_y or top < min_visible_y:
            self.widget.yview_moveto((top - self.thumb_h) / max_y)



if __name__ == "__main__":
    from db import FileDatabase

    db = FileDatabase('master.sqlite')
    li = db.search_by_tags(['tausta'])
    li = db.get_full_paths(li)
    tk = Tk()

    tk.bind('<Control-q>', lambda e: tk.quit())
    tk.rowconfigure(0, weight=1)
    tk.columnconfigure(0, weight=1)
    if sys.argv[1] == 'slide':
        ss = SlideShow(tk, li)
        ss.widget.focus_set()
        ss.widget.grid(column=0, row=0, sticky=(N, W, E, S))
    elif sys.argv[1] == 'gallery':
        g = Gallery(tk, li, (180,180), lambda l: show(l))
        def show(li):
            ss = SlideShow(tk, [g.get_path(i) for i in li])
            ss.widget.focus_set()
            ss.widget.winfo_width = g.widget.winfo_width
            ss.widget.winfo_height = g.widget.winfo_height
            ss.widget.grid(column=0, row=0)
            ss.widget.bind('<q>', lambda e: ss.widget.destroy())
            ss.widget.bind('<Destroy>', lambda e: g.widget.focus_set())

        g.widget.grid(column=0, row=0, sticky=(N, W, E, S))
        g.widget.focus_set()
        sb = Scrollbar(tk, command = g.widget.yview)
        g.widget['yscrollcommand'] = sb.set
        sb.grid(column=1, row=0, sticky=(N,S))
    tk.mainloop()

