#!/usr/bin/python
#-*- coding: UTF-8 -*-

"""cicm - Console Image Collection Manager
Cicm is a free software that creates, edits
and manages image collections. It's also a
sample ui for xfclib. See readme.txt
for usage guide"""

__author__  = "Tachara (tortured.flame@gmail.com)"
__date__ = "$Date 2010/31/03 18:07:00 $"
__copyright__ = "Copyright (c) 2010 Tachara"

import sys
import os

from db import FileDatabase
from gui2db import Gui2Db
from tkgui import Main
from tkgraphics import gallery_with_slideshow
from tagview import TagView

import keybindings

if __name__ == "__main__":

    dbname = 'master.sqlite'
    if len(sys.argv) > 1:
        dbname = sys.argv[1]
    db = FileDatabase(dbname)
    mainview = Main()

    glue = Gui2Db(db, mainview)

    tags = db.list_tags()
    tview = TagView(mainview.sidebar, tags)

    actions = {
        'quit' : lambda e: mainview.quit(),
        'next_view' : lambda e: mainview.next_view(),
        'delete_view': mainview.delete_current_view,
        'add_tags' : lambda e: mainview.text_query('Add tags: '),
        'add_images' : glue.add_files,
        'add_folder' : glue.add_directory,
        'remove_tags': glue.remove_tags_from_files,
        'jump_to_tag': lambda e: mainview.text_query('Jump to tag: ',
            accept_func=lambda t, o: tview.jump_to(t))
        'focus_sidebar': lambda e: mainview.sidebar_views[0].widget.focus_set(),
        'toggle_selection_tags': glue.toggle_selection_tags,
    }
    keybindings.make_bindings(keybindings.appwide, actions, mainview.root.bind_all)
    buttons = {
            'Remove deleted': glue.remove_deleted_files,
    }
    for label in buttons:
        mainview.add_menubutton(label, buttons[label])

    # Custom virtual events do not need to be user bindable
    # since their generation is user bindable. -> no dictionaries used.
    mainview.root.bind_all('<<TagViewSearch>>', glue.search)
    mainview.root.bind_all('<<TagViewEdit>>',
            lambda e: mainview.text_query('Edit tag:', tview.selection()[0]))
    mainview.root.bind_all('<<MainQueryAccept>>', glue.add_or_rename_tags)
    mainview.root.bind_all('<<GallerySelectionChanged>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowNext>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowPrev>>', glue.update_selection_tags)

    mainview.add_sidebar(tview)
    mainview.display()

