
import os
import sys
import warnings
from math import floor
from collections import namedtuple
import logging
logger = logging.getLogger(__name__)

try:
    from Tkinter import *
    from ttk import *
except ImportError:
    from tkinter import *
    from tkinter.ttk import *

from PIL import Image
from PIL.ImageTk import PhotoImage

import keybindings as kb

MouseWheelEvent = 38

Cursor = namedtuple('Cursor', ['column', 'row', 'prev_item', 'cid'])
def resize(image, target_height, target_width):
    image.thumbnail((target_width, target_height), Image.BILINEAR)

def gallery_creator(new_view):
    return lambda root, paths: Gallery(root, paths, (250, 250),
            lambda s, a: new_view(SlideShow(root, s, a)))

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
        kb.bind('slideshow', (self, ), self.widget.bind)

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

    def close(self):
        if self._tid is not None:
            self.widget.after_cancel(self._tid)


    
class Gallery(object):
    LIMIT = 1000
    DELAY = 100

    def __init__(self, root, paths, thumb_size, activate_func):
        """thumb_size = (w, h)"""
        self.paths = paths
        self.thumb_w = thumb_size[0]
        self.thumb_h = thumb_size[1]
        self.photos = list()
        self._selection = set()
        self.widget = Frame(root, takefocus=1)
        self.make_view()
        kb.bind('gallery', (self, ), self.bind)
        self._canvas.bind('<Configure>', lambda e: self.reload())
        self.activate_func = activate_func
        self._canvas.configure(takefocus=1)
        self.loaded = 0
        self._select_mode = False
        self._load_tid = None
        self._repos_tid = None

    def bind(self, *args, **kwargs):
        self._canvas.bind(*args, **kwargs)
        self.widget.bind(*args, **kwargs)

    def make_view(self):
        self.style = Style()
        self.style.configure('Gallery.TLabel', padding=3)
        self.style.configure('Cursor.Gallery.TLabel', background='red')
        self.style.configure('Selected.Gallery.TLabel', background='blue')
        self._canvas = Canvas(self.widget)
        self._canvas.grid(row=0, column=0, sticky=(N,W,S,E))
        self.widget.rowconfigure(0, weight=1)
        self.widget.columnconfigure(0,weight=1)
        self._canvas['confine'] = True
        self.prev_w = self._canvas.winfo_width()
        self.load_pos = 0
        self.row = 0
        self.column = 0
        self.cursor = Cursor(-1,-1,-1, '')
        self._scroll = Scrollbar(self.widget, command=self._canvas.yview, takefocus=0)
        self._canvas['yscrollcommand'] = self._scroll.set
        self._scroll.grid(row=0, column=1, sticky=(N,S))
        self.widget.columnconfigure(1, weight=0)
        self.max_columns = self.calculate_max_columns()
        self.widget.after(self.DELAY, self.load_next)

    def activate(self, e):
        photo_index = self.cursor_to_index(self.cursor.row, self.cursor.column)
        selection = self.selection()
        active_index = selection.index(self.paths[self.photos[photo_index].path_index])
        self.activate_func(selection, active_index)
        self._canvas.focus_set()

    def get_path(self, item_id):
        return self.paths[item_id]

    def selection(self):
        logger.debug('selection %s', str(self._selection))
        paths = list()
        photo_index = self.cursor_to_index(self.cursor.row, self.cursor.column)
        if photo_index not in self._selection and self.cursor.row != -1:
            paths.append(self.paths[self.photos[photo_index].path_index])
        if len(self._selection) > 0:
            paths.extend([self.paths[self.photos[i].path_index] for i in self._selection])
        return paths

    def clear_selection(self):
        self._canvas.dtag('selected', 'selected')
        for index in self._selection:
            self.set_state(self.photos[index], 'normal')
        self._selection.clear()

    def toggle_selection(self, event):
        photo_index = self.cursor_to_index(self.cursor.row, self.cursor.column)
        if photo_index in self._selection:
            self.selection_remove(self.photos[photo_index])
        else:
            self.selection_add(self.photos[photo_index])

    def button_callback(self, event):
        if event.num == 5 or event.num == 4 or event.type == MouseWheelEvent:
            self.scroll(event)
            return
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        cid = self._canvas.find_closest(x, y)[0]
        def cmpr(p):
            if p.cid != cid:
                if hasattr(p, 'rectangle_id'):
                    return p.rectangle_id == cid
            else:
                return True
            return False
        item = next(filter(cmpr, self.photos),
            self.photos[self.cursor_to_index(self.cursor.row, self.cursor.column)])
        row, column = divmod(item.index, self.max_columns)
        self.set_cursor(item, column, row)

    def scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self._canvas.yview(SCROLL, -1, UNITS)
        elif event.num == 5 or event.delta < 0:
            self._canvas.yview(SCROLL, 1, UNITS)

    def reload(self):
        w = self._canvas.winfo_width()
        if w != self.prev_w:
            self.prev_w = w
            self.max_columns = self.calculate_max_columns()
            self.repos = 0
            self.repos_col = 0
            self.repos_row = 0
            self._repos_tid = self.widget.after(self.DELAY, self.reposition_next)

    def reposition_next(self):
        if len(self.photos) > 0:
            photo = self.photos[self.repos]
            new_x, new_y = self.calculate_pos(self.repos_col, self.repos_row)
            self._canvas.coords(photo.cid, new_x, new_y)
            rectangle = getattr(photo, 'rectangle_id', None)
            if rectangle is not None:
                bbox = self._canvas.bbox(photo.cid)
                self._canvas.coords(rectangle, bbox[0], bbox[1], bbox[2], bbox[3])
            if self.repos == self.cursor.prev_item:
                self.cursor = Cursor(self.repos_col, self.repos_row, self.repos, self.cursor.cid)
            col, row = self.repos_col, self.repos_row
            self.repos_col += 1

        if self.repos_col >= self.max_columns:
            self.repos_row += 1
            self.repos_col = 0
        if self.repos < len(self.photos) - 1:
            self.repos += 1
            self._repos_tid = self.widget.after(self.DELAY, self.reposition_next)
        else:
            new_x, new_y = self.calculate_pos(self.repos_col, self.repos_row)
            self._canvas.coords('loadbutton', new_x, new_y)
            self._canvas['scrollregion'] = self._canvas.bbox('all')
            if self.cursor.prev_item != -1:
                index = self.cursor_to_index(self.cursor.row, self.cursor.column)
                self.view_item(self.photos[index])

    def calculate_max_columns(self):
        w = self._canvas.winfo_width()
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
            photo.cid = self._canvas.create_image(x, y, image=photo)
            photo.index = len(self.photos) - 1
            photo.path_index = self.load_pos
            self._canvas.addtag_withtag('photo', photo.cid)
            self.column += 1
            self.loaded += 1
        except OSError:
            logger.info('Could not open %s', self.paths[self.load_pos])
            self.load_pos += 1
        except Image.DecompressionBombWarning:
            self.load_pos += 1

        if self.column >= self.max_columns:
            self.row += 1
            self.column = 0
        if self.load_pos < len(self.paths) - 1 and self.loaded <= self.LIMIT:
            self.load_pos += 1
            self._load_tid = self.widget.after(self.DELAY, self.load_next)
        elif self.loaded >= self.LIMIT:
            self.loaded = 0
            x, y = self.calculate_pos(self.column, self.row)
            button = Button(self._canvas, text='Load More', command=self.continue_loading)
            cid = self._canvas.create_window(x, y, window=button)
            self._canvas.addtag_withtag('loadbutton', cid)
        else:
            self._load_tid = None
        self._canvas['scrollregion'] = self._canvas.bbox('all')

    def continue_loading(self):
        if self.load_pos < len(self.paths) - 1:
            self.load_pos += 1
            self._canvas.delete('loadbutton')
            self._canvas.after(self.DELAY, self.load_next)

    def cursor_to_index(self, row, column):
        if row == -1:
            return 0
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
        new_index = self.cursor_to_index(row, column)
        if new_index >= len(self.photos):
            row, column = self.max_cursor_position()
            new_index = len(self.photos) - 1
        elif new_index < 0:
            row, column = 0, 0
            new_index = 0
        logger.debug('move_cursor, new_index=%d', new_index)
        item = self.photos[new_index]
        logger.debug('move_cursor, item.index=%d', item.index)
        self.set_cursor(item, column, row)

    def set_cursor(self, item, column, row, index=None):
        cid = self.cursor.cid
        bbox = self._canvas.bbox(item.cid)
        if cid == '':
            color = 'red'
            cid = self._canvas.create_rectangle(bbox[0], bbox[1], bbox[2], bbox[3],
                    outline=color, fill=color, stipple='gray12', width=3)
        else:
            self._canvas.coords(cid,bbox[0], bbox[1], bbox[2], bbox[3])
        if self._select_mode:
            self.selection_add(item)
        rect = getattr(item, 'rectangle_id', None)
        if rect is not None:
            self._canvas.tag_raise(cid, rect)
        else:
            self._canvas.tag_raise(cid, item.cid)
        self.cursor = Cursor(column, row, index or row*self.max_columns + column, cid)
        logger.debug('cursor: %s', str(self.cursor))
        self._canvas.event_generate('<<GallerySelectionChanged>>')
        self.view_item(item)

    def toggle_select_mode(self):
        self._select_mode = not self._select_mode
        if self._select_mode and self.cursor.cid != '':
            ind = self.cursor_to_index(self.cursor.row, self.cursor.column)
            self.selection_add(self.photos[ind])

    def selection_add(self, item):
        self._selection.add(item.index)
        self.set_state(item, 'selected')
        self._canvas.event_generate('<<GallerySelectionChanged>>')

    def selection_remove(self, item):
        self._selection.remove(item.index)
        self.set_state(item, 'normal')
        self._canvas.dtag(item.cid, 'selected')
        self._canvas.event_generate('<<GallerySelectionChanged>>')

    def set_state(self, item, state):
        color = ''
        if state == 'selected':
            color = 'blue'

        rect = getattr(item, 'rectangle_id', '')
        if rect == '':
            bbox = self._canvas.bbox(item.cid)
            item.rectangle_id = self._canvas.create_rectangle(bbox[0], bbox[1], bbox[2], bbox[3],
                    outline=color, fill=color,stipple='gray75', width=10)
            self._canvas.tag_raise(item.rectangle_id, item.cid)
        else:
            self._canvas.itemconfigure(rect, outline=color, fill=color)

    def view_item(self, item):
        self._canvas['scrollregion'] = self._canvas.bbox('all')
        bbox = self._canvas.bbox(item.cid)
        max_y = self._canvas.bbox('all')[3]
        max_visible_y = self._canvas.canvasy(self._canvas.winfo_height())
        min_visible_y = self._canvas.canvasy(0)
        top = bbox[1]
        bottom = bbox[3]
        if bottom > max_visible_y or top < min_visible_y:
            self._canvas.yview_moveto((top - self.thumb_h) / max_y)

    def close(self):
        if self._load_tid is not None:
            self.widget.after_cancel(self._load_tid)
        if self._repos_tid is not None:
            self.widget.after_cancel(self._repos_tid)

