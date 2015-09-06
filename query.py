
from tkinter import N, S, W, E, END, StringVar
from tkinter.ttk import Frame, Entry, Label

from tagview import NameView
import keybindings as kb

class ListStringQuery:

    def __init__(self, master, query_label, original_text=None, complete_list=None):
        self.widget = Frame(master)
        label = Label(self.widget, text=query_label)
        label.grid(column=0, row=0, sticky=(N, S))

        self.text_var = StringVar()
        entry = None
        if complete_list is not None:
            self.nameview = NameView(self.widget, complete_list)
            self.nameview.widget.grid(row=1, column=0, columnspan=2, sticky=(N,S,W,E))
            ok_command = self.widget.register(self.is_ok)
            self.entry = Entry(self.widget, textvariable=self.text_var,
                    validatecommand=(ok_command, '%P'), validate='key')
        else:
            self.entry = Entry(self.widget, textvariable=self.text_var)

        if original_text is not None:
            self.text_var.set(original_text)
        self.entry.original_value = original_text
        self.entry.grid(column=1, row=0, sticky=(N,S,W,E))
        self.widget.columnconfigure(1, weight=1)
        self.widget.rowconfigure(1, weight=1)
        kb.bind('text_query', (self, ), self.entry.bind)

        self.entry.focus_set()

    def accept_completion(self, event=None):
        selection = self.nameview.selection()
        content = self.entry.get()
        items = content.split(',')
        items[-1] = selection[0]
        self.text_var.set(','.join(items))
        self.entry.focus_set()
        self.entry.icursor(END)
        # Prevents the event from propagating further.
        return 'break'

    def accept(self, event):
        self.entry.event_generate('<<ListStringQueryAccept>>')
        
    def cancel(self, event):
        self.entry.event_generate('<<ListStringQueryCancel>>')

    def is_ok(self, content):
        items = content.split(',')
        self.nameview.filter(items[-1])
        self.nameview.focus_next()
        self.nameview.select()
        return True
