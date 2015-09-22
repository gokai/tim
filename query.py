
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
        if complete_list is not None:
            self.nameview = NameView(self.widget, sorted(complete_list))
            self.nameview.widget.grid(row=1, column=0, columnspan=2, sticky=(N,S,W,E))
            ok_command = self.widget.register(self.is_ok)
            self.entry = Entry(self.widget, textvariable=self.text_var,
                    validatecommand=(ok_command, '%P'), validate='key')
        else:
            self.entry = Entry(self.widget, textvariable=self.text_var)
            self.nameview = None

        if original_text is not None:
            self.text_var.set(original_text)
        self.entry.original_value = original_text
        self.entry.grid(column=1, row=0, sticky=(N,S,W,E))
        self.widget.columnconfigure(1, weight=1)
        self.widget.rowconfigure(1, weight=1)
        kb.bind('text_query', (self, ), self.entry.bind)
        self.entry.icursor(END)

    def accept_completion(self, event=None):
        if self.nameview is not None:
            selection = self.nameview.selection()
            if len(selection) > 0:
                content = self.entry.get()
                items = content.split(',')
                if len(items) > 0:
                    items[-1] = selection[0]
                else:
                    items.append(selection[0])
                self.text_var.set(','.join(items))
                self.entry.focus_set()
                self.entry.icursor(END)
                self.entry.after(3, lambda : self.entry.xview(END))
            # Prevents the event from propagating further.
            return 'break'

    def next_completion(self, event):
        if self.nameview is not None:
            self.nameview.clear_selection()
            self.nameview.focus_next()
            self.nameview.select()

    def prev_completion(self, event):
        if self.nameview is not None:
            self.nameview.clear_selection()
            self.nameview.focus_prev()
            self.nameview.select()

    def accept(self, event):
        self.entry.event_generate('<<ListStringQueryAccept>>')
        
    def cancel(self, event):
        self.entry.event_generate('<<ListStringQueryCancel>>')

    def is_ok(self, content):
        self.nameview.clear_selection()
        items = content.split(',')
        self.nameview.filter(items[-1])
        self.nameview.focus_first()
        self.nameview.select()
        return True

