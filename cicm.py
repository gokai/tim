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

    dbname = 'winexperiment.sqlite'
    db = FileDatabase(dbname)
    mainview = Main()

    glue = Gui2Db(db, mainview)

    tags = db.list_tags()
    tview = TagView(mainview, tags)

    actions = {
        'quit' : lambda e: mainview.quit(),
        'next_view' : lambda e: mainview.next_view(),
        'delete_view': mainview.delete_current_view,
        'add_tags' : lambda e: mainview.text_query('Add tags: '),
        'add_images' : glue.add_files,
        'add_folder' : glue.add_directory,
    }
    keybindings.make_bindings(keybindings.appwide, actions, mainview.root.bind_all)

    # Custom virtual events do not need to be user bindable
    # since their generation is user bindable. -> no dictionaries used.
    mainview.root.bind_all('<<TagViewSearch>>', glue.search)
    mainview.root.bind_all('<<TagViewEdit>>', lambda e: mainview.text_query('Edit tag:', e.widget.selection()[0]))
    mainview.root.bind_all('<<MainQueryAccept>>', glue.add_or_rename_tags)

    mainview.add_sidebar(tview)
    mainview.display()

