
from tkinter import N, S, W, E, END
from tkinter.ttk import Frame, Label, Entry

from query import ListStringQuery
import keybindings as kb

class CollectionEditView:

    def __init__(self, root, collection, tags, all_tags, update_func):
        self.old_name = collection
        self.old_tags = tags
        self.update = update_func
        self.widget = Frame(root)
        self.widget.rowconfigure(2, weight=1)
        self.widget.columnconfigure(1, weight=1)

        main_label = Label(self.widget, text='Collection edit')
        main_label.grid(row=0, column=0, columnspan=2)
        name_label = Label(self.widget, text='Name: ')
        name_label.grid(row=1, column=0)
        self._name_entry = Entry(self.widget)
        self._name_entry.insert(0, collection)
        self._name_entry.icursor(END)
        self._name_entry.grid(row=1, column=1, sticky=(N, S, W, E))

        self._tag_entry = ListStringQuery(self.widget, 'Tags: ', 
                original_text=','.join(tags), complete_list=all_tags)
        self.widget.bind_all('<<ListStringQueryAccept>>', self.accept)
        self.widget.bind_all('<<ListStringQueryCancel>>', self.cancel)
        self._tag_entry.widget.grid(row=2, column=0, columnspan=2, sticky=(N, S, W, E))
        kb.bind('collection_edit', (self, ), self.bind)
        self._name_entry.focus_set()
        self._focused = 'n'

    def bind(self, *args, **kwargs):
        self.widget.bind(*args, **kwargs)
        self._name_entry.bind(*args, **kwargs)
        self._tag_entry.entry.bind(*args, **kwargs)

    def accept(self, event):
        self.update(self)
        self.close()
    
    def cancel(self, event):
        self.close()

    def switch_focus(self, event):
        if self._focused == 'n':
            self._focused = 't'
            self._tag_entry.entry.focus_set()
        else:
            self._focused = 'n'
            self._name_entry.focus_set()
        return 'break'

    def new_tags(self):
        return self._tag_entry.entry.get().split(',')
    
    def new_name(self):
        return self._name_entry.get()

    def close(self):
        self.widget.unbind('<<ListStringQueryAccept>>')
        self.widget.unbind('<<ListStringQueryCancel>>')
        self.widget.event_generate('<<CollectionEditClose>>')

